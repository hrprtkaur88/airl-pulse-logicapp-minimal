using Azure.Identity;
using Azure.Monitor.OpenTelemetry.AspNetCore;
using Azure.Storage.Blobs;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Azure.Cosmos;
using Microsoft.Identity.Web;
using Microsoft.Identity.Web.UI;
using Microsoft.IdentityModel.Protocols;
using Microsoft.IdentityModel.Protocols.OpenIdConnect;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using AirlPulseReport.Web.Services;

var builder = WebApplication.CreateBuilder(args);

// --- Web host: 1-year HSTS + preload, request-size cap ------------------
builder.Services.Configure<Microsoft.AspNetCore.HttpsPolicy.HstsOptions>(o =>
{
    o.MaxAge = TimeSpan.FromDays(365);
    o.IncludeSubDomains = true;
    o.Preload = true;
});
builder.WebHost.ConfigureKestrel(k =>
{
    k.AddServerHeader = false;               // strip "Server: Kestrel"
    k.Limits.MaxRequestBodySize = 10_000_000; // 10 MB hard cap
});

// --- Entra ID sign-in for the portal ------------------------------------
builder.Services
    .AddAuthentication(OpenIdConnectDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApp(builder.Configuration.GetSection("AzureAd"));

builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser()
        .Build();
});

builder.Services
    .AddRazorPages()
    .AddMicrosoftIdentityUI();

// --- Admin JWT validation config (used by /admin/* middleware below) -----
var tenantId = builder.Configuration["AzureAd:TenantId"]
    ?? throw new InvalidOperationException("Missing AzureAd:TenantId");
var clientId = builder.Configuration["AzureAd:ClientId"]
    ?? throw new InvalidOperationException("Missing AzureAd:ClientId");
var allowedAdminOids = (builder.Configuration["Admin:AllowedPrincipalIds"] ?? "")
    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
    .ToHashSet(StringComparer.OrdinalIgnoreCase);

var oidcConfigManager = new ConfigurationManager<OpenIdConnectConfiguration>(
    $"https://login.microsoftonline.com/{tenantId}/v2.0/.well-known/openid-configuration",
    new OpenIdConnectConfigurationRetriever());
builder.Services.AddSingleton(oidcConfigManager);

var adminValidationParams = new TokenValidationParameters
{
    ValidateIssuer   = true,
    ValidateAudience = true,
    ValidateLifetime = true,
    ValidateIssuerSigningKey = true,
    ValidAudiences   = new[] { $"api://{clientId}", clientId },
    ValidIssuers     = new[]
    {
        $"https://login.microsoftonline.com/{tenantId}/v2.0",
        $"https://sts.windows.net/{tenantId}/",
    },
};

// --- Azure credential (MSI in Azure, azd/local principal in dev) --------
var cred = new DefaultAzureCredential(includeInteractiveCredentials: false);

// --- Cosmos client (per-app singleton) ----------------------------------
var cosmosEndpoint = builder.Configuration["Cosmos:Endpoint"]
    ?? throw new InvalidOperationException("Missing Cosmos:Endpoint");
builder.Services.AddSingleton(_ => new CosmosClient(cosmosEndpoint, cred,
    new CosmosClientOptions
    {
        ApplicationName = "airl-pulse-report-web",
        SerializerOptions = new CosmosSerializationOptions
        {
            PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase,
        }
    }));
builder.Services.AddSingleton<CosmosUserService>();

// --- Blob client for report container -----------------------------------
var storageAccount = builder.Configuration["Storage:Account"]
    ?? throw new InvalidOperationException("Missing Storage:Account");
builder.Services.AddSingleton(_ => new BlobServiceClient(
    new Uri($"https://{storageAccount}.blob.core.windows.net/"), cred));
builder.Services.AddSingleton<BlobReportService>();

// --- Application Insights (workspace-based) ------------------------------
var appiConn = builder.Configuration["ApplicationInsights:ConnectionString"];
if (!string.IsNullOrWhiteSpace(appiConn))
{
    builder.Services.AddOpenTelemetry().UseAzureMonitor(o => o.ConnectionString = appiConn);
}

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    // 1-year HSTS + preload eligibility.
    app.UseHsts();
}

// --- Security headers (applied to every response) ----------------------
app.Use(async (ctx, next) =>
{
    var h = ctx.Response.Headers;
    // Info-disclosure: strip server banner.
    h.Remove("Server");
    h.Remove("X-Powered-By");
    // Enterprise headers.
    h["X-Content-Type-Options"] = "nosniff";
    h["X-Frame-Options"]        = "DENY";
    h["Referrer-Policy"]        = "no-referrer";
    h["Permissions-Policy"]     = "camera=(), microphone=(), geolocation=(), interest-cohort=()";
    h["X-Robots-Tag"]           = "noindex, nofollow";
    h["Cross-Origin-Opener-Policy"]  = "same-origin";
    h["Cross-Origin-Resource-Policy"] = "same-origin";
    h["Content-Security-Policy"] =
        "default-src 'self'; " +
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " +
        "script-src 'self' https://cdn.jsdelivr.net; " +
        "img-src 'self' data:; " +
        "connect-src 'self' https://login.microsoftonline.com; " +
        "frame-ancestors 'none'; " +
        "base-uri 'self'; " +
        "form-action 'self' https://login.microsoftonline.com";
    await next();
    // Remove Server *after* the pipeline in case a downstream middleware re-added it.
    // Guard with HasStarted: streamed responses (e.g. /report/latest) may already have
    // written headers + begun the body by the time next() returns, and mutating headers
    // at that point throws InvalidOperationException ("response has already started"),
    // which previously surfaced to the client as a 502.
    if (!ctx.Response.HasStarted)
    {
        ctx.Response.Headers.Remove("Server");
    }
});

// --- Admin JWT gate: any /admin/* request must present a valid Entra Bearer
//     token whose oid claim matches an allow-listed principal ID
//     (typically the Logic App's system-assigned MSI). Runs BEFORE the OIDC
//     middleware so failures return 401, not a sign-in redirect.
app.Use(async (ctx, next) =>
{
    if (!ctx.Request.Path.StartsWithSegments("/admin"))
    {
        await next();
        return;
    }

    var authz = ctx.Request.Headers["Authorization"].ToString();
    if (string.IsNullOrWhiteSpace(authz) || !authz.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
    {
        ctx.Response.StatusCode = 401;
        ctx.Response.Headers["WWW-Authenticate"] = $"Bearer realm=\"admin\", audience=\"api://{clientId}\"";
        await ctx.Response.WriteAsJsonAsync(new { error = "missing Bearer token" });
        return;
    }

    var token = authz.Substring("Bearer ".Length).Trim();
    try
    {
        var oidcConfig = await oidcConfigManager.GetConfigurationAsync(ctx.RequestAborted);
        var validation = adminValidationParams.Clone();
        validation.IssuerSigningKeys = oidcConfig.SigningKeys;

        var handler = new JwtSecurityTokenHandler();
        var principal = handler.ValidateToken(token, validation, out _);

        var oid = principal.FindFirst("oid")?.Value
                  ?? principal.FindFirst("http://schemas.microsoft.com/identity/claims/objectidentifier")?.Value;
        if (string.IsNullOrEmpty(oid) || !allowedAdminOids.Contains(oid))
        {
            ctx.Response.StatusCode = 403;
            await ctx.Response.WriteAsJsonAsync(new { error = "principal not authorized for /admin/*" });
            return;
        }

        ctx.User = principal;
    }
    catch (Exception ex) when (ex is SecurityTokenException
                            || ex is ArgumentException
                            || ex is FormatException)
    {
        ctx.Response.StatusCode = 401;
        ctx.Response.Headers["WWW-Authenticate"] =
            $"Bearer realm=\"admin\", error=\"invalid_token\", error_description=\"{ex.GetType().Name}\"";
        await ctx.Response.WriteAsJsonAsync(new { error = "invalid Bearer token" });
        return;
    }

    await next();
});

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthentication();
app.UseAuthorization();
app.MapRazorPages();
app.MapControllers();

// Signed-in proxy for the current user's latest report.
// Emits a locked-down CSP specifically on this response so any LLM-injected
// <script> in the report HTML cannot exfiltrate cookies or call out.
app.MapGet("/report/latest", async (HttpContext http, CosmosUserService users, BlobReportService reports, CancellationToken ct) =>
{
    var email = http.User.FindFirst("preferred_username")?.Value
                ?? http.User.FindFirst(System.Security.Claims.ClaimTypes.Email)?.Value;
    if (string.IsNullOrWhiteSpace(email)) return Results.Redirect("/Unauthorized");
    var user = await users.FindByEmailAsync(email, ct);
    if (user is null) return Results.Redirect("/Unauthorized");
    var payload = await reports.DownloadLatestReportAsync(user.ClientName, ct);
    if (payload is null) return Results.NotFound($"No report available for {user.ClientName}");

    // Sandbox the served HTML — no scripts, no external resource loads.
    http.Response.Headers["Content-Security-Policy"] =
        "default-src 'none'; " +
        "style-src 'unsafe-inline'; " +
        "img-src data:; " +
        "font-src data:; " +
        "sandbox";
    http.Response.Headers["X-Frame-Options"] = "DENY";
    return Results.Stream(payload.Value.Content, payload.Value.ContentType);
}).RequireAuthorization();

// Admin endpoints — already gated by the JWT middleware above.
// AllowAnonymous prevents the OIDC-redirect fallback authorization policy
// from being layered on top of our JWT check.
app.MapPost("/admin/upload-report", async (HttpRequest req, BlobServiceClient bsc, IConfiguration cfg) =>
{
    var container = cfg["Storage:ReportContainer"] ?? "report";
    var path = req.Query["path"].ToString();
    if (string.IsNullOrWhiteSpace(path))
        return Results.BadRequest("missing ?path=<slug>/report-file-<key>.html");

    // Strict path allowlist — prevents traversal (../ or absolute) and enforces the
    // canonical <slug>/<name>.html shape used everywhere else in the app.
    var allowed = System.Text.RegularExpressions.Regex.IsMatch(
        path, @"^[a-z0-9][a-z0-9\-]{0,63}/report-file-(latest|\d{8})\.html$");
    if (!allowed)
        return Results.BadRequest("path must match ^<slug>/report-file-(latest|DDMMYYYY).html$");

    if (req.ContentLength.HasValue && req.ContentLength.Value > 5_000_000)
        return Results.StatusCode(StatusCodes.Status413PayloadTooLarge);

    using var ms = new MemoryStream();
    await req.Body.CopyToAsync(ms);
    ms.Position = 0;
    var blob = bsc.GetBlobContainerClient(container).GetBlobClient(path);
    await blob.UploadAsync(ms, overwrite: true);
    await blob.SetHttpHeadersAsync(new Azure.Storage.Blobs.Models.BlobHttpHeaders
    {
        ContentType = "text/html; charset=utf-8"
    });
    return Results.Ok(new { path, container });
}).AllowAnonymous();

app.MapGet("/admin/list-blobs", async (HttpRequest req, BlobServiceClient bsc) =>
{
    var container = req.Query["container"].ToString();
    if (string.IsNullOrWhiteSpace(container)) container = "data";
    var ct = bsc.GetBlobContainerClient(container);
    var list = new List<object>();
    await foreach (var b in ct.GetBlobsAsync())
    {
        list.Add(new { name = b.Name, size = b.Properties.ContentLength, modified = b.Properties.LastModified });
    }
    return Results.Ok(new { container, count = list.Count, items = list });
}).AllowAnonymous();

app.MapGet("/admin/list-users", async (CosmosClient cosmosClient, IConfiguration cfg, CancellationToken ct) =>
{
    var db = cfg["Cosmos:Database"] ?? "reporting";
    var container = cfg["Cosmos:UsersContainer"] ?? "users";
    var ct2 = cosmosClient.GetContainer(db, container);
    var results = new List<object>();
    var iter = ct2.GetItemQueryIterator<Dictionary<string, object>>(
        "SELECT c.email, c.client_id, c.client_name, c.user_name FROM c");
    while (iter.HasMoreResults)
    {
        foreach (var row in await iter.ReadNextAsync(ct))
        {
            results.Add(row);
        }
    }
    return Results.Ok(results);
}).AllowAnonymous();

app.Run();

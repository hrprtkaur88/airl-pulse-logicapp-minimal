using System.Security.Claims;
using AirlPulseReport.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace AirlPulseReport.Web.Pages;

public class IndexModel : PageModel
{
    private readonly CosmosUserService _users;
    private readonly BlobReportService _reports;
    private readonly ILogger<IndexModel> _log;

    public IndexModel(CosmosUserService users, BlobReportService reports, ILogger<IndexModel> log)
    {
        _users = users;
        _reports = reports;
        _log = log;
    }

    public AirlUser? SignedInUser { get; private set; }
    public bool ReportAvailable { get; private set; }

    public async Task<IActionResult> OnGetAsync(CancellationToken ct)
    {
        var email = HttpContext.User.FindFirst("preferred_username")?.Value
                    ?? HttpContext.User.FindFirst(ClaimTypes.Email)?.Value;
        if (string.IsNullOrWhiteSpace(email))
        {
            _log.LogWarning("No email claim on signed-in user");
            return RedirectToPage("/Unauthorized");
        }

        var user = await _users.FindByEmailAsync(email, ct);
        if (user is null)
        {
            _log.LogInformation("User {Email} not authorized", email);
            return RedirectToPage("/Unauthorized");
        }

        SignedInUser = user;
        ReportAvailable = await _reports.LatestReportExistsAsync(user.ClientName, ct);
        return Page();
    }
}

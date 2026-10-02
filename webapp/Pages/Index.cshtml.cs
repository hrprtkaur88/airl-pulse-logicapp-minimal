using AirlPulseReport.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace AirlPulseReport.Web.Pages;

public class IndexModel : PageModel
{
    private const int PageSize = 10;

    private readonly GroupAccessService _groupAccess;
    private readonly ClientDirectoryService _clientDirectory;
    private readonly IConfiguration _cfg;
    private readonly ILogger<IndexModel> _log;

    public IndexModel(GroupAccessService groupAccess, ClientDirectoryService clientDirectory, IConfiguration cfg, ILogger<IndexModel> log)
    {
        _groupAccess = groupAccess;
        _clientDirectory = clientDirectory;
        _cfg = cfg;
        _log = log;
    }

    public string? DisplayName { get; private set; }
    public List<(string ClientId, string ClientName)> AccessibleCompanies { get; private set; } = new();
    public bool IsAdmin { get; private set; }

    public string? SelectedClientId { get; private set; }
    public string? SelectedClientName { get; private set; }
    /// <summary>Reports for the selected company, newest first, already paged to the current page.</summary>
    public List<ReportRow> PagedReports { get; private set; } = new();
    public int CurrentPage { get; private set; } = 1;
    public int TotalPages { get; private set; } = 1;

    public record ReportRow(string FileName, string Label, bool IsLatest);

    public async Task<IActionResult> OnGetAsync(string? client, int page, CancellationToken ct)
    {
        DisplayName = HttpContext.User.FindFirst("name")?.Value
                      ?? HttpContext.User.FindFirst("preferred_username")?.Value
                      ?? HttpContext.User.Identity?.Name;

        var groupIds = EntraGroupClaims.GetGroupIds(HttpContext.User);

        var adminGroupId = _cfg["Admin:AdminGroupId"];
        IsAdmin = !string.IsNullOrWhiteSpace(adminGroupId) && groupIds.Contains(adminGroupId);

        AccessibleCompanies = await _groupAccess.GetAccessibleClientsAsync(groupIds, ct);
        if (AccessibleCompanies.Count == 0 && !IsAdmin)
        {
            _log.LogInformation("Signed-in user has no group_access mapping for any of their {Count} groups", groupIds.Count);
            return RedirectToPage("/Unauthorized");
        }
        if (AccessibleCompanies.Count == 0) return Page();

        // Resolve which company's reports to show: the requested ?client=, if
        // the caller is actually authorized for it, else their first
        // accessible company. Never trusts ?client= beyond membership testing
        // against AccessibleCompanies (computed purely from group_access).
        var match = !string.IsNullOrWhiteSpace(client)
            ? AccessibleCompanies.FirstOrDefault(c => string.Equals(c.ClientId, client, StringComparison.OrdinalIgnoreCase))
            : default;
        var selected = match.ClientId is not null ? match : AccessibleCompanies[0];
        SelectedClientId = selected.ClientId;
        SelectedClientName = selected.ClientName;

        var entry = await _clientDirectory.GetAsync(selected.ClientId, ct);
        var allReports = entry?.ReportFiles ?? new List<string>();

        CurrentPage = page < 1 ? 1 : page;
        TotalPages = allReports.Count == 0 ? 1 : (int)Math.Ceiling(allReports.Count / (double)PageSize);
        if (CurrentPage > TotalPages) CurrentPage = TotalPages;

        PagedReports = allReports
            .Skip((CurrentPage - 1) * PageSize)
            .Take(PageSize)
            .Select((fileName, idx) => new ReportRow(fileName, LabelFor(fileName), IsLatest: CurrentPage == 1 && idx == 0))
            .ToList();

        return Page();
    }

    private static string LabelFor(string fileName)
    {
        // report-file-DDMMYYYY.html -> "20 Sep 2026"
        var m = System.Text.RegularExpressions.Regex.Match(fileName, @"report-file-(\d{2})(\d{2})(\d{4})\.html");
        if (!m.Success) return fileName;
        var day = int.Parse(m.Groups[1].Value);
        var month = int.Parse(m.Groups[2].Value);
        var year = int.Parse(m.Groups[3].Value);
        try
        {
            var date = new DateOnly(year, month, day);
            return date.ToString("dd MMM yyyy");
        }
        catch (ArgumentOutOfRangeException)
        {
            return fileName;
        }
    }
}

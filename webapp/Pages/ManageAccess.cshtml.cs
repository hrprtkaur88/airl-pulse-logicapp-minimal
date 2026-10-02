using AirlPulseReport.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace AirlPulseReport.Web.Pages;

/// <summary>
/// Interactive admin portal for managing which Entra security groups can
/// view which company's report (the group_access Cosmos container) and for
/// maintaining the known-company directory (the clients Cosmos container).
/// Deliberately NOT named "/Admin*" -- that prefix is reserved by the
/// machine-to-machine JWT gate middleware in Program.cs (any path under
/// "/admin" there requires a bearer token, not a browser cookie session),
/// so an admin-prefixed route here would be unreachable by a signed-in
/// human being redirected through the normal OIDC flow.
///
/// Authorization: the signed-in user must be a member of the Entra
/// security group configured in Admin:AdminGroupId (the "groups" claim on
/// their ID token -- see EntraGroupClaims). Checked manually in each
/// handler (matching the existing IndexModel pattern) rather than via an
/// [Authorize] policy, so an unauthorized-but-authenticated user gets the
/// same friendly /Unauthorized page as everywhere else in this app instead
/// of a bare 403.
///
/// Laid out as three Bootstrap tabs (client-side only, via
/// bootstrap.bundle.min.js's data-bs-toggle="tab" -- no server round trip
/// to switch tabs):
///   1. Client Directory -- sync from Blob storage, correct display names.
///      Paginated (10/page) like the home page's report list.
///   2. Existing Mappings -- every group->company mapping, editable in place
///      (group name, target company, contact email) and deletable.
///      Also paginated (10/page).
///   3. Add New Mapping -- create a mapping for a new Entra group. The
///      company dropdown here always lists EVERY known client (unpaginated)
///      -- pagination applies only to the two review/browse tables above,
///      never to a picker the admin needs the full list to search through.
/// ActiveTab controls which tab is shown active after a full-page postback
/// or a pagination link click (?tab=1|2|3&dirPage=&mapPage=).
/// </summary>
public class ManageAccessModel : PageModel
{
    private const int PageSize = 10;

    private readonly GroupAccessService _groupAccess;
    private readonly ClientDirectoryService _clientDirectory;
    private readonly IConfiguration _cfg;
    private readonly ILogger<ManageAccessModel> _log;

    public ManageAccessModel(GroupAccessService groupAccess, ClientDirectoryService clientDirectory, IConfiguration cfg, ILogger<ManageAccessModel> log)
    {
        _groupAccess = groupAccess;
        _clientDirectory = clientDirectory;
        _cfg = cfg;
        _log = log;
    }

    /// <summary>Every mapping, unpaginated -- used only to populate dropdowns.</summary>
    public List<GroupAccessMapping> Mappings { get; private set; } = new();
    /// <summary>Every known client, unpaginated -- used only to populate dropdowns.</summary>
    public List<ClientDirectoryEntry> KnownClients { get; private set; } = new();

    public List<ClientDirectoryEntry> PagedClients { get; private set; } = new();
    public int DirPage { get; private set; } = 1;
    public int DirTotalPages { get; private set; } = 1;

    public List<GroupAccessMapping> PagedMappings { get; private set; } = new();
    public int MapPage { get; private set; } = 1;
    public int MapTotalPages { get; private set; } = 1;

    /// <summary>1 = Client Directory, 2 = Existing Mappings, 3 = Add New Mapping.</summary>
    public int ActiveTab { get; private set; } = 1;

    [BindProperty] public string NewGroupId { get; set; } = "";
    [BindProperty] public string NewGroupName { get; set; } = "";
    [BindProperty] public string NewClientId { get; set; } = "";
    [BindProperty] public string NewContactEmail { get; set; } = "";

    public string? StatusMessage { get; private set; }
    public bool StatusIsError { get; private set; }

    private bool IsCallerAdmin()
    {
        var adminGroupId = _cfg["Admin:AdminGroupId"];
        if (string.IsNullOrWhiteSpace(adminGroupId)) return false;
        return EntraGroupClaims.GetGroupIds(HttpContext.User).Contains(adminGroupId);
    }

    private async Task LoadAsync(CancellationToken ct, int dirPage = 1, int mapPage = 1)
    {
        Mappings = await _groupAccess.ListAllAsync(ct);
        KnownClients = await _clientDirectory.ListAsync(ct);

        DirTotalPages = KnownClients.Count == 0 ? 1 : (int)Math.Ceiling(KnownClients.Count / (double)PageSize);
        DirPage = Math.Clamp(dirPage, 1, DirTotalPages);
        PagedClients = KnownClients.Skip((DirPage - 1) * PageSize).Take(PageSize).ToList();

        MapTotalPages = Mappings.Count == 0 ? 1 : (int)Math.Ceiling(Mappings.Count / (double)PageSize);
        MapPage = Math.Clamp(mapPage, 1, MapTotalPages);
        PagedMappings = Mappings.Skip((MapPage - 1) * PageSize).Take(PageSize).ToList();
    }

    private static bool LooksLikeEmail(string value) =>
        !string.IsNullOrWhiteSpace(value) && value.Contains('@') && !value.Contains(' ');

    public async Task<IActionResult> OnGetAsync(int dirPage, int mapPage, int tab, CancellationToken ct)
    {
        if (!IsCallerAdmin())
        {
            _log.LogInformation("Non-admin attempted to access /ManageAccess");
            return RedirectToPage("/Unauthorized");
        }
        ActiveTab = tab is 1 or 2 or 3 ? tab : 1;
        await LoadAsync(ct, dirPage < 1 ? 1 : dirPage, mapPage < 1 ? 1 : mapPage);
        return Page();
    }

    public async Task<IActionResult> OnPostAddAsync(CancellationToken ct)
    {
        if (!IsCallerAdmin()) return RedirectToPage("/Unauthorized");
        ActiveTab = 3;

        if (string.IsNullOrWhiteSpace(NewGroupId) || string.IsNullOrWhiteSpace(NewGroupName) || string.IsNullOrWhiteSpace(NewClientId))
        {
            StatusMessage = "Group object ID, group display name, and a selected company are all required.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }
        if (!Guid.TryParse(NewGroupId.Trim(), out _))
        {
            StatusMessage = "Group object ID must be a GUID (copy it from the group's Overview page in Entra ID).";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }
        if (!string.IsNullOrWhiteSpace(NewContactEmail) && !LooksLikeEmail(NewContactEmail))
        {
            StatusMessage = "Contact email doesn't look like a valid email address.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }

        var client = (await _clientDirectory.ListAsync(ct)).FirstOrDefault(c => c.ClientId == NewClientId);
        if (client is null)
        {
            StatusMessage = "Selected company was not found in the client directory -- try syncing first.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }

        await _groupAccess.AddAsync(NewGroupId.Trim(), NewGroupName.Trim(), client.ClientId, client.ClientName, NewContactEmail.Trim(), ct);
        StatusMessage = $"Added: \"{NewGroupName.Trim()}\" -> {client.ClientName}.";
        NewGroupId = ""; NewGroupName = ""; NewClientId = ""; NewContactEmail = "";
        await LoadAsync(ct);
        return Page();
    }

    public async Task<IActionResult> OnPostEditMappingAsync(string id, string groupId, string editGroupName, string editClientId, string editContactEmail, CancellationToken ct)
    {
        if (!IsCallerAdmin()) return RedirectToPage("/Unauthorized");
        ActiveTab = 2;

        if (string.IsNullOrWhiteSpace(editGroupName) || string.IsNullOrWhiteSpace(editClientId))
        {
            StatusMessage = "Group display name and company are required.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }
        if (!string.IsNullOrWhiteSpace(editContactEmail) && !LooksLikeEmail(editContactEmail))
        {
            StatusMessage = "Contact email doesn't look like a valid email address.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }

        var client = (await _clientDirectory.ListAsync(ct)).FirstOrDefault(c => c.ClientId == editClientId);
        if (client is null)
        {
            StatusMessage = "Selected company was not found in the client directory.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }

        await _groupAccess.UpdateAsync(id, groupId, editGroupName.Trim(), client.ClientId, client.ClientName, editContactEmail?.Trim() ?? "", ct);
        StatusMessage = $"Updated: \"{editGroupName.Trim()}\" -> {client.ClientName}.";
        await LoadAsync(ct);
        return Page();
    }

    public async Task<IActionResult> OnPostDeleteAsync(string id, string groupId, CancellationToken ct)
    {
        if (!IsCallerAdmin()) return RedirectToPage("/Unauthorized");
        ActiveTab = 2;

        await _groupAccess.DeleteAsync(id, groupId, ct);
        StatusMessage = "Mapping removed.";
        await LoadAsync(ct);
        return Page();
    }

    public async Task<IActionResult> OnPostSyncClientsAsync(CancellationToken ct)
    {
        if (!IsCallerAdmin()) return RedirectToPage("/Unauthorized");
        ActiveTab = 1;

        var discovered = await _clientDirectory.SyncFromStorageAsync(ct);
        StatusMessage = discovered.Count == 0
            ? "Synced -- no new companies found in storage (report lists refreshed for all known companies)."
            : $"Synced -- discovered {discovered.Count} new compan{(discovered.Count == 1 ? "y" : "ies")}: {string.Join(", ", discovered)}.";
        await LoadAsync(ct);
        return Page();
    }

    public async Task<IActionResult> OnPostRenameClientAsync(string clientId, string newName, CancellationToken ct)
    {
        if (!IsCallerAdmin()) return RedirectToPage("/Unauthorized");
        ActiveTab = 1;

        if (string.IsNullOrWhiteSpace(clientId) || string.IsNullOrWhiteSpace(newName))
        {
            StatusMessage = "Client ID and new name are required.";
            StatusIsError = true;
            await LoadAsync(ct);
            return Page();
        }

        await _clientDirectory.UpdateNameAsync(clientId, newName.Trim(), ct);
        StatusMessage = $"Renamed {clientId} to \"{newName.Trim()}\".";
        await LoadAsync(ct);
        return Page();
    }
}

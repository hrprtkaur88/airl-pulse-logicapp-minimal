using Microsoft.Azure.Cosmos;
using Azure.Storage.Blobs;

namespace AirlPulseReport.Web.Services;

public record ClientDirectoryEntry(string ClientId, string ClientName, string Source, DateTimeOffset LastSynced, List<string> ReportFiles);

/// <summary>
/// Authoritative list of known companies, sourced from the real client
/// folders in Blob "data" (the same container Synapse's export pipeline and
/// ai-foundry/jobs/run_batch.py write assessment workbooks into --
/// ai-foundry/jobs/run_batch.py's list_clients_from_data() enumerates these
/// same top-level folders to discover which clients to process each month).
/// Cached into a Cosmos "clients" container so the Admin portal's company
/// picker is a reviewed, typo-proof dropdown instead of free text, and so a
/// storage scan isn't required on every page load.
///
/// Client display names are NOT reliably recoverable from blob storage
/// alone -- the folder name is always the slug (e.g. "acme-corp"), not the
/// legal/display name. SyncFromStorageAsync seeds a best-effort
/// de-slugified suggestion ("Acme Corp") for any newly-discovered client
/// and otherwise leaves the stored client_name untouched, so an admin's
/// manual correction (via UpdateNameAsync) survives repeated syncs.
///
/// Each client document also caches a report_files array (blob file names,
/// newest first) refreshed on every sync by scanning Blob "report" -- see
/// BlobReportService.ListReportFilesAsync. The home page reads this cached
/// array (cheap Cosmos point-read) instead of listing blobs on every page
/// view; "Sync from storage" in the Admin portal is what keeps it current.
/// </summary>
public class ClientDirectoryService
{
    private readonly Container _container;
    private readonly BlobContainerClient _dataContainer;
    private readonly BlobReportService _reports;

    public ClientDirectoryService(CosmosClient cosmosClient, BlobServiceClient bsc, BlobReportService reports, IConfiguration cfg)
    {
        var db = cfg["Cosmos:Database"] ?? throw new InvalidOperationException("Cosmos:Database");
        var ct = cfg["Cosmos:ClientsContainer"] ?? "clients";
        _container = cosmosClient.GetContainer(db, ct);

        var dataContainerName = cfg["Storage:DataContainer"] ?? "data";
        _dataContainer = bsc.GetBlobContainerClient(dataContainerName);
        _reports = reports;
    }

    public async Task<List<ClientDirectoryEntry>> ListAsync(CancellationToken ct = default)
    {
        var results = new List<ClientDirectoryEntry>();
        using var iter = _container.GetItemQueryIterator<Dictionary<string, object>>(
            "SELECT c.client_id, c.client_name, c.source, c.last_synced, c.report_files FROM c");
        while (iter.HasMoreResults)
        {
            foreach (var row in await iter.ReadNextAsync(ct))
            {
                results.Add(new ClientDirectoryEntry(
                    row["client_id"]?.ToString() ?? "",
                    row["client_name"]?.ToString() ?? "",
                    row.TryGetValue("source", out var s) ? s?.ToString() ?? "" : "",
                    row.TryGetValue("last_synced", out var t) && DateTimeOffset.TryParse(t?.ToString(), out var dto) ? dto : default,
                    ParseReportFiles(row)));
            }
        }
        return results.OrderBy(c => c.ClientName, StringComparer.OrdinalIgnoreCase).ToList();
    }

    public async Task<ClientDirectoryEntry?> GetAsync(string clientId, CancellationToken ct = default)
    {
        try
        {
            var resp = await _container.ReadItemAsync<Dictionary<string, object>>(clientId, new PartitionKey(clientId), cancellationToken: ct);
            var row = resp.Resource;
            return new ClientDirectoryEntry(
                row["client_id"]?.ToString() ?? "",
                row["client_name"]?.ToString() ?? "",
                row.TryGetValue("source", out var s) ? s?.ToString() ?? "" : "",
                row.TryGetValue("last_synced", out var t) && DateTimeOffset.TryParse(t?.ToString(), out var dto) ? dto : default,
                ParseReportFiles(row));
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    private static List<string> ParseReportFiles(Dictionary<string, object> row)
    {
        if (!row.TryGetValue("report_files", out var raw) || raw is null) return new();
        if (raw is System.Text.Json.JsonElement je && je.ValueKind == System.Text.Json.JsonValueKind.Array)
            return je.EnumerateArray().Select(e => e.GetString() ?? "").Where(v => v.Length > 0).ToList();
        if (raw is IEnumerable<object> list)
            return list.Select(v => v?.ToString() ?? "").Where(v => v.Length > 0).ToList();
        return new();
    }

    /// <summary>
    /// Scans Blob "data" for top-level client folders and upserts any not
    /// already known, then refreshes the report_files array for EVERY known
    /// client (new reports land for existing clients every month, so this
    /// isn't limited to newly-discovered ones). Returns the newly-discovered
    /// client IDs. Existing entries keep their current client_name (only
    /// last_synced/report_files are refreshed) so an admin's manual name
    /// correction is never overwritten.
    /// </summary>
    public async Task<List<string>> SyncFromStorageAsync(CancellationToken ct = default)
    {
        var existing = (await ListAsync(ct)).Select(c => c.ClientId).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var discovered = new List<string>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var now = DateTimeOffset.UtcNow;

        await foreach (var item in _dataContainer.GetBlobsByHierarchyAsync(delimiter: "/", cancellationToken: ct))
        {
            if (item.IsPrefix != true) continue;
            var slug = item.Prefix.TrimEnd('/');
            if (string.IsNullOrWhiteSpace(slug)) continue;
            seen.Add(slug);

            if (!existing.Contains(slug))
            {
                discovered.Add(slug);
            }
        }

        // Refresh report_files for every currently-known client (new + existing),
        // not just newly-discovered ones, since new monthly reports land for
        // clients that were already in the directory.
        foreach (var slug in existing.Union(seen, StringComparer.OrdinalIgnoreCase))
        {
            Dictionary<string, object> doc;
            try
            {
                var current = await _container.ReadItemAsync<Dictionary<string, object>>(slug, new PartitionKey(slug), cancellationToken: ct);
                doc = current.Resource;
            }
            catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                doc = new Dictionary<string, object>
                {
                    ["id"] = slug,
                    ["client_id"] = slug,
                    ["client_name"] = DeslugifySuggestion(slug),
                    ["source"] = "blob:data",
                };
            }

            var clientName = doc["client_name"]?.ToString() ?? DeslugifySuggestion(slug);
            var reportFiles = await _reports.ListReportFilesAsync(clientName, ct);
            doc["last_synced"] = now.ToString("O");
            doc["report_files"] = reportFiles.Select(r => r.FileName).ToList();
            await _container.UpsertItemAsync(doc, new PartitionKey(slug), cancellationToken: ct);
        }

        return discovered;
    }

    public async Task UpdateNameAsync(string clientId, string newName, CancellationToken ct = default)
    {
        var current = await _container.ReadItemAsync<Dictionary<string, object>>(clientId, new PartitionKey(clientId), cancellationToken: ct);
        current.Resource["client_name"] = newName;
        await _container.UpsertItemAsync(current.Resource, new PartitionKey(clientId), cancellationToken: ct);
    }

    private static string DeslugifySuggestion(string slug) =>
        string.Join(" ", slug.Split('-', StringSplitOptions.RemoveEmptyEntries)
            .Select(w => w.Length == 0 ? w : char.ToUpperInvariant(w[0]) + w[1..]));
}


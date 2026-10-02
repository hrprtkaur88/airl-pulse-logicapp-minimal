using Microsoft.Azure.Cosmos;

namespace AirlPulseReport.Web.Services;

/// <summary>
/// A single Entra security group -> company mapping. One company can have
/// multiple groups (e.g. a "Viewers" and an "Executives" group), and --
/// the point of this feature -- one user can be a member of several
/// groups, each granting a different company, so a single sign-in can
/// surface several companies' reports.
/// </summary>
public record GroupAccessMapping(string Id, string GroupId, string GroupName, string ClientId, string ClientName, string ContactEmail);

/// <summary>
/// Replaces the old one-row-per-user Cosmos model (client_id/client_name
/// tied directly to a single user's email) with a group-to-company mapping
/// table. Access is computed at request time as the union of companies
/// mapped to any Entra security group the signed-in user belongs to (the
/// "groups" claim on their ID token -- see Program.cs's groupMembershipClaims
/// configuration on the app registration). The old "users" container/
/// CosmosUserService is left in place, unused by new authorization logic,
/// rather than deleted.
/// </summary>
public class GroupAccessService
{
    private readonly Container _container;

    public GroupAccessService(CosmosClient client, IConfiguration cfg)
    {
        var db = cfg["Cosmos:Database"] ?? throw new InvalidOperationException("Cosmos:Database");
        var ct = cfg["Cosmos:GroupAccessContainer"] ?? "group_access";
        _container = client.GetContainer(db, ct);
    }

    /// <summary>
    /// Distinct companies accessible to a user who belongs to any of the
    /// given Entra group IDs. Empty input -> empty result (no groups, no
    /// access) rather than an all-rows scan.
    /// </summary>
    public async Task<List<(string ClientId, string ClientName)>> GetAccessibleClientsAsync(
        IEnumerable<string> groupIds, CancellationToken ct = default)
    {
        var ids = groupIds.Distinct().ToList();
        if (ids.Count == 0) return new();

        // IN (...) with a parameterized list -- Cosmos SQL supports this via
        // ARRAY_CONTAINS with a parameter array, which also avoids building
        // dynamic SQL text from user-influenced group ID values.
        var query = new QueryDefinition("SELECT c.client_id, c.client_name FROM c WHERE ARRAY_CONTAINS(@ids, c.group_id)")
            .WithParameter("@ids", ids);

        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var results = new List<(string, string)>();
        using var iter = _container.GetItemQueryIterator<Dictionary<string, object>>(query);
        while (iter.HasMoreResults)
        {
            foreach (var row in await iter.ReadNextAsync(ct))
            {
                var clientId = row["client_id"]?.ToString() ?? "";
                var clientName = row["client_name"]?.ToString() ?? "";
                if (clientId.Length == 0 || !seen.Add(clientId)) continue;
                results.Add((clientId, clientName));
            }
        }
        return results.OrderBy(r => r.Item2, StringComparer.OrdinalIgnoreCase).ToList();
    }

    /// <summary>Every mapping, for the Admin portal's management table.</summary>
    public async Task<List<GroupAccessMapping>> ListAllAsync(CancellationToken ct = default)
    {
        var results = new List<GroupAccessMapping>();
        using var iter = _container.GetItemQueryIterator<Dictionary<string, object>>(
            "SELECT c.id, c.group_id, c.group_name, c.client_id, c.client_name, c.contact_email FROM c");
        while (iter.HasMoreResults)
        {
            foreach (var row in await iter.ReadNextAsync(ct))
            {
                results.Add(new GroupAccessMapping(
                    row["id"]?.ToString() ?? "",
                    row["group_id"]?.ToString() ?? "",
                    row["group_name"]?.ToString() ?? "",
                    row["client_id"]?.ToString() ?? "",
                    row["client_name"]?.ToString() ?? "",
                    row.TryGetValue("contact_email", out var e) ? e?.ToString() ?? "" : ""));
            }
        }
        return results
            .OrderBy(m => m.ClientName, StringComparer.OrdinalIgnoreCase)
            .ThenBy(m => m.GroupName, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    /// <summary>
    /// Adds a mapping for an already-known client (clientId/clientName come
    /// from ClientDirectoryService's vetted list, selected via a dropdown in
    /// the Admin portal -- never free-typed -- so this never has to guess or
    /// re-derive a slug). contactEmail is an optional group-owner/distribution
    /// contact recorded for reference only -- it is NOT used for anything
    /// security-relevant (report delivery uses the Cosmos "users"/synced
    /// per-recipient data, not this field).
    /// </summary>
    public async Task<GroupAccessMapping> AddAsync(string groupId, string groupName, string clientId, string clientName, string contactEmail, CancellationToken ct = default)
    {
        var doc = new Dictionary<string, object>
        {
            ["id"] = Guid.NewGuid().ToString(),
            ["group_id"] = groupId,
            ["group_name"] = groupName,
            ["client_id"] = clientId,
            ["client_name"] = clientName,
            ["contact_email"] = contactEmail ?? "",
        };
        await _container.UpsertItemAsync(doc, new PartitionKey(groupId), cancellationToken: ct);
        return new GroupAccessMapping(doc["id"].ToString()!, groupId, groupName, clientId, clientName, contactEmail ?? "");
    }

    /// <summary>
    /// Edits an existing mapping's group name, target company, and/or contact
    /// email. group_id (the partition key) and the document id are immutable --
    /// to repoint a mapping at a different Entra group, delete and re-add.
    /// </summary>
    public async Task<GroupAccessMapping> UpdateAsync(string id, string groupId, string groupName, string clientId, string clientName, string contactEmail, CancellationToken ct = default)
    {
        var doc = new Dictionary<string, object>
        {
            ["id"] = id,
            ["group_id"] = groupId,
            ["group_name"] = groupName,
            ["client_id"] = clientId,
            ["client_name"] = clientName,
            ["contact_email"] = contactEmail ?? "",
        };
        await _container.UpsertItemAsync(doc, new PartitionKey(groupId), cancellationToken: ct);
        return new GroupAccessMapping(id, groupId, groupName, clientId, clientName, contactEmail ?? "");
    }

    public async Task DeleteAsync(string id, string groupId, CancellationToken ct = default)
    {
        await _container.DeleteItemAsync<Dictionary<string, object>>(id, new PartitionKey(groupId), cancellationToken: ct);
    }
}

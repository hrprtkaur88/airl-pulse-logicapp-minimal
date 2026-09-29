using Microsoft.Azure.Cosmos;

namespace AirlPulseReport.Web.Services;

public record AirlUser(string Id, string ClientId, string ClientName, string UserName, string Email);

public class CosmosUserService
{
    private readonly Container _container;

    public CosmosUserService(CosmosClient client, IConfiguration cfg)
    {
        var db = cfg["Cosmos:Database"] ?? throw new InvalidOperationException("Cosmos:Database");
        var ct = cfg["Cosmos:UsersContainer"] ?? throw new InvalidOperationException("Cosmos:UsersContainer");
        _container = client.GetContainer(db, ct);
    }

    public async Task<AirlUser?> FindByEmailAsync(string email, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(email)) return null;
        var query = new QueryDefinition(
            "SELECT TOP 1 c.id, c.client_id, c.client_name, c.user_name, c.email " +
            "FROM c WHERE LOWER(c.email) = @e"
        ).WithParameter("@e", email.ToLowerInvariant());

        using var iter = _container.GetItemQueryIterator<CosmosUserRecord>(query,
            requestOptions: new QueryRequestOptions { MaxItemCount = 1 });
        while (iter.HasMoreResults)
        {
            foreach (var rec in await iter.ReadNextAsync(ct))
            {
                return new AirlUser(rec.id, rec.client_id, rec.client_name, rec.user_name, rec.email);
            }
        }
        return null;
    }

    private record CosmosUserRecord(string id, string client_id, string client_name, string user_name, string email);
}

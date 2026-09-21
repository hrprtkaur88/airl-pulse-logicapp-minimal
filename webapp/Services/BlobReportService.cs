using Azure.Storage.Blobs;
using AirlPulseReport.Shared;

namespace AirlPulseReport.Web.Services;

public class BlobReportService
{
    private readonly BlobContainerClient _reportContainer;

    public BlobReportService(BlobServiceClient bsc, IConfiguration cfg)
    {
        var container = cfg["Storage:ReportContainer"] ?? "report";
        _reportContainer = bsc.GetBlobContainerClient(container);
    }

    public async Task<bool> LatestReportExistsAsync(string clientName, CancellationToken ct = default)
    {
        var blob = _reportContainer.GetBlobClient(Naming.ReportLatestPath(clientName));
        return await blob.ExistsAsync(ct);
    }

    /// <summary>
    /// Server-side proxy: signed-in web app streams the client's latest HTML report
    /// via its managed identity through the private endpoint. Never exposes the storage key.
    /// </summary>
    public async Task<(Stream Content, string ContentType)?> DownloadLatestReportAsync(string clientName, CancellationToken ct = default)
    {
        var blob = _reportContainer.GetBlobClient(Naming.ReportLatestPath(clientName));
        if (!await blob.ExistsAsync(ct)) return null;
        var resp = await blob.DownloadStreamingAsync(cancellationToken: ct);
        var ctType = resp.Value.Details.ContentType ?? "text/html";
        return (resp.Value.Content, ctType);
    }
}

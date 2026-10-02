using Azure.Storage.Blobs;
using AirlPulseReport.Shared;

namespace AirlPulseReport.Web.Services;

/// <summary>One dated report entry for a client, newest first.</summary>
public record ReportEntry(string FileName, DateOnly? ReportDate, bool IsLatest);

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

    /// <summary>
    /// Streams any single report file for a client by its exact blob file name
    /// (e.g. "report-file-20092026.html" or "report-file-latest.html"). Callers
    /// MUST validate the file name against the canonical
    /// report-file-(latest|DDMMYYYY).html pattern before calling this --
    /// see Program.cs's ReportFileNamePattern -- this method does not
    /// re-validate, it only resolves <clientName's slug>/<fileName>.
    /// </summary>
    public async Task<(Stream Content, string ContentType)?> DownloadReportByNameAsync(string clientName, string fileName, CancellationToken ct = default)
    {
        var path = $"{Naming.Slugify(clientName)}/{fileName}";
        var blob = _reportContainer.GetBlobClient(path);
        if (!await blob.ExistsAsync(ct)) return null;
        var resp = await blob.DownloadStreamingAsync(cancellationToken: ct);
        var ctType = resp.Value.Details.ContentType ?? "text/html";
        return (resp.Value.Content, ctType);
    }

    /// <summary>
    /// Lists every report file blob for a client directly from storage (used by
    /// ClientDirectoryService's sync to refresh the cached report_files array --
    /// live callers should read that Cosmos-cached array instead of calling this
    /// on every page load). Sorted newest-first by the DDMMYYYY date encoded in
    /// the file name; "report-file-latest.html" is excluded since it duplicates
    /// whichever dated file is most recent.
    /// </summary>
    public async Task<List<ReportEntry>> ListReportFilesAsync(string clientName, CancellationToken ct = default)
    {
        var prefix = $"{Naming.Slugify(clientName)}/";
        var entries = new List<ReportEntry>();
        await foreach (var blob in _reportContainer.GetBlobsAsync(prefix: prefix, cancellationToken: ct))
        {
            var fileName = blob.Name[prefix.Length..];
            var match = System.Text.RegularExpressions.Regex.Match(fileName, @"^report-file-(\d{2})(\d{2})(\d{4})\.html$");
            if (!match.Success) continue;
            var day = int.Parse(match.Groups[1].Value);
            var month = int.Parse(match.Groups[2].Value);
            var year = int.Parse(match.Groups[3].Value);
            DateOnly? date = null;
            try { date = new DateOnly(year, month, day); } catch (ArgumentOutOfRangeException) { /* skip malformed date, keep file listed without a parsed date */ }
            entries.Add(new ReportEntry(fileName, date, IsLatest: false));
        }
        return entries.OrderByDescending(e => e.ReportDate).ToList();
    }
}


using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace AirlPulseReport.Shared;

/// <summary>
/// Canonical slug rule for client_name used in every blob path.
/// Define once, everywhere else must call <see cref="Slugify"/>.
/// </summary>
public static class Naming
{
    private static readonly Regex NonAlnum = new("[^a-z0-9]+", RegexOptions.Compiled);

    public static string Slugify(string clientName)
    {
        if (string.IsNullOrWhiteSpace(clientName))
            throw new ArgumentException("clientName is required", nameof(clientName));

        var normalized = clientName.Trim().ToLowerInvariant().Normalize(NormalizationForm.FormD);
        var sb = new StringBuilder(normalized.Length);
        foreach (var ch in normalized)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark)
                sb.Append(ch);
        }
        var slug = NonAlnum.Replace(sb.ToString(), "-").Trim('-');
        return slug;
    }

    public static string DataCsvPath(string clientName, string monthKeyMMYYYY) =>
        $"{Slugify(clientName)}/export-file-{monthKeyMMYYYY}.csv";

    /// <summary>
    /// Path for the AIRL assessment workbook (.xlsx) consumed by
    /// ai-foundry/skill/scripts/build_content_model.py. Supersedes
    /// DataCsvPath now that the pipeline generates AIRL-shaped workbooks
    /// instead of flat transactional CSVs.
    /// </summary>
    public static string DataWorkbookPath(string clientName, string monthKeyMMYYYY) =>
        $"{Slugify(clientName)}/assessment-workbook-{monthKeyMMYYYY}.xlsx";

    public static string ReportDatedPath(string clientName, string dateKeyDDMMYYYY) =>
        $"{Slugify(clientName)}/report-file-{dateKeyDDMMYYYY}.html";

    public static string ReportLatestPath(string clientName) =>
        $"{Slugify(clientName)}/report-file-latest.html";

    public static string StatusManifestPath(string clientName, string monthKeyMMYYYY) =>
        $"{Slugify(clientName)}/status-{monthKeyMMYYYY}.json";
}

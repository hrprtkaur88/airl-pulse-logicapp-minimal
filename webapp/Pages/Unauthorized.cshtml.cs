using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace AirlPulseReport.Web.Pages;

[AllowAnonymous]
public class UnauthorizedModel : PageModel
{
    public string SupportEmail { get; }

    public UnauthorizedModel(IConfiguration cfg)
    {
        SupportEmail = cfg["Support:Email"] ?? "support@example.com";
    }
}

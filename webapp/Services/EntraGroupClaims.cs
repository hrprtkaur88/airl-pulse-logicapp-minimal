using System.Security.Claims;

namespace AirlPulseReport.Web.Services;

/// <summary>
/// Reads Entra security-group object IDs from the "groups" claim on the
/// signed-in user's ID token. Requires the app registration's
/// groupMembershipClaims property to be set to "SecurityGroup" (or "All") --
/// see notebooks/deploy.ipynb / README for the one-time `az ad app update`
/// command. Note: this reflects group membership as of the last sign-in/
/// token refresh, not live membership -- a user added to a group needs a
/// fresh sign-in before it takes effect.
///
/// Known limitation: Entra emits an overage indicator instead of the
/// "groups" claim when a user belongs to more than ~150-200 groups. This
/// tenant/app is far below that threshold; if it ever becomes a concern,
/// the fix is to switch to Microsoft Graph's POST /me/checkMemberGroups
/// (delegated GroupMember.Read.All, which requires tenant admin consent --
/// not available to this deployment's automation identity at the time this
/// was built).
/// </summary>
public static class EntraGroupClaims
{
    public static HashSet<string> GetGroupIds(ClaimsPrincipal user) =>
        user.Claims.Where(c => c.Type == "groups").Select(c => c.Value)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
}

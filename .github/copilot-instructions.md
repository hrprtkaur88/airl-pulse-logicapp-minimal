# Copilot instructions for this repository

See [`AGENTS.md`](../AGENTS.md) at the repo root for the full set of agent
instructions -- it covers the webapp UI theme conventions (Bootstrap 5.3,
`webapp/wwwroot/css/theme.css`, button/size standards) and the dependency
security policy (NuGet vulnerability scanning, Bootstrap CDN SRI hashes).
Follow it for any change under `webapp/`.

Quick summary for Copilot code review / chat in this repo:

- Never introduce page-specific CSS for colors, buttons, tables, or
  pagination in the webapp -- reuse the standard Bootstrap classes
  (`btn-primary`, `btn-outline-dark`, `btn-outline-danger`, `.card` +
  `.card-header`, `.table`, `.pagination`) which are already themed
  globally by `webapp/wwwroot/css/theme.css`.
- Never use the Bootstrap `-sm` size variants outside the navbar
  (`_LoginPartial.cshtml`'s Sign in/out button is the one exception).
- Before completing a dependency change, run
  `dotnet list webapp package --vulnerable --include-transitive` and fix
  any reported advisory.
- If you bump the Bootstrap CDN version in
  `webapp/Pages/Shared/_Layout.cshtml`, recompute the SRI `integrity` hash
  for both the CSS and JS files -- do not reuse the previous hash.

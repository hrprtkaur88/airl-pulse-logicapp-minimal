# Agent instructions for this repository

These instructions apply to any AI coding agent (GitHub Copilot, Claude,
Cursor, or similar) making changes in this repo. `.github/copilot-instructions.md`
points back here for GitHub Copilot specifically -- keep both in sync if you
change one.

## webapp UI: one theme, no per-page CSS

All ASP.NET Razor Pages UI lives under `webapp/Pages/`, uses Bootstrap 5.3
loaded from a CDN, and is themed by exactly one file:
**`webapp/wwwroot/css/theme.css`**. Read the comment block at the top of
that file before touching any page markup -- it explains *why* the theme
works the way it does (Bootstrap 5.3's compiled CSS sets colors as local
CSS variables per component, e.g. `.btn-primary{--bs-btn-bg:...}`, not from
a single global `--bs-primary` token, so theming must override those local
component tokens, not just root variables).

**Never add page-specific or component-specific color/spacing CSS.** If a
new page needs a button, table, card, tab, or pagination control, reuse the
existing Bootstrap classes below -- the shared theme.css already makes them
match the Korn Ferry brand everywhere:

| Need | Use |
|---|---|
| Primary / "do the main thing" action (Add, Save, Switch, View, Submit) | `class="btn btn-primary"` |
| Neutral / secondary action (Sync, Cancel) | `class="btn btn-outline-dark"` |
| Destructive action (Remove, Delete) | `class="btn btn-outline-danger"` |
| A titled content section on an admin/management page | Wrap it in `<div class="card"><div class="card-header">Title</div><div class="card-body">...</div></div>` -- never bare content directly on the page background |
| A browsable/editable list | `<table class="table">` (+ `table-striped`, `align-middle` as needed) with Bootstrap `.pagination` if there's more than one page |

**Never use the `-sm` (small) size variant** (`btn-sm`, `form-control-sm`,
`form-select-sm`, `pagination-sm`, `table-sm`) outside the navbar. The
navbar's Sign in/out button (`_LoginPartial.cshtml`) is the one intentional
exception -- compact controls are normal for a slim dark navbar. Everywhere
else, mixing regular and `-sm` controls on different tabs/pages of the same
app is a real, measurable inconsistency (different pixel heights), not just
a subjective one -- it has been the root cause of "buttons don't line up"
bug reports in this app before. If you're unsure whether two controls now
match, don't just eyeball a screenshot -- measure them (e.g. via
`getBoundingClientRect()` in a quick browser check) and confirm equal
heights before calling it done.

If Bootstrap's stock classes genuinely don't cover a new need, add the
override to `theme.css` using the same pattern already there (override the
component's own `--bs-*` local tokens, e.g. `--bs-btn-bg`, not a bare
`background-color`), and update the CONVENTIONS block comment in that file
so the next person/agent knows the new pattern exists.

## Dependency security

- Keep NuGet packages (`webapp/AirlPulseReport.Web.csproj`,
  `ai-foundry/function/*.csproj` if present) free of known-vulnerable
  versions. Before finishing any change that touches dependencies, or
  periodically, run:
  ```powershell
  dotnet list <project> package --vulnerable --include-transitive
  ```
  and resolve any reported advisory by bumping to a patched version (check
  for transitive version conflicts this can introduce, e.g. `Azure.Core`
  brought in by both `Azure.Identity` and `Azure.Monitor.OpenTelemetry.*`
  -- align both to compatible versions and rebuild).
- Keep the Bootstrap CDN `<link>`/`<script>` versions in
  `webapp/Pages/Shared/_Layout.cshtml` reasonably current (check
  https://github.com/twbs/bootstrap/releases). Whenever you change the
  version, **recompute the SRI `integrity` hash** for both the CSS and JS
  bundle -- never guess or reuse an old hash:
  ```powershell
  Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@<version>/dist/css/bootstrap.min.css" -OutFile bootstrap.min.css
  $hash = (Get-FileHash -Algorithm SHA384 bootstrap.min.css).Hash
  [Convert]::ToBase64String([System.Convert]::FromHexString($hash))
  ```
  (repeat for `bootstrap.bundle.min.js`), then prefix the result with
  `sha384-`.

## Verifying UI changes

This app requires interactive Entra ID sign-in, so unit tests
(`tests/webapp.unit`) cover services/handlers but not rendered layout.
After any theme or markup change:
1. `dotnet test tests/webapp.unit -c Release` (must stay green).
2. `dotnet build -c Release webapp` with zero warnings/errors.
3. Deploy to the dev Web App (`az webapp deploy ... --type zip`) and verify
   live with a browser tool across **all** affected tabs/pages -- not just
   the one you edited. Take a full-page screenshot of each tab/page you
   touched, or measure key element heights/colors directly, and actually
   look at the result before reporting the change as done. Cross-tab
   button/table/header consistency has repeatedly needed a second pass in
   this app when only one tab was checked.

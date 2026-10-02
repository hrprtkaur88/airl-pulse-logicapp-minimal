// Index.cshtml's company-selector form. Changing the dropdown no longer
// auto-submits -- it immediately hides the (now-stale) report list/heading
// for the previously-selected company and shows a hint, so a signed-in
// user is never shown one company's report list mislabeled or left
// looking current while it actually belongs to whichever company was
// selected before. The full, fresh list only reappears after a real page
// navigation triggered by clicking "Switch" (a plain form submit).
//
// Kept as an external file (not inline event-handler attributes) because
// the app's Content-Security-Policy (Program.cs) sets script-src 'self'
// without 'unsafe-inline' -- CSP blocks inline handlers the same way it
// blocks inline <script> blocks.
document.addEventListener('DOMContentLoaded', function () {
    var select = document.getElementById('companySelect');
    var results = document.getElementById('reportsResults');
    var heading = document.getElementById('selectedCompanyHeading');
    var hint = document.getElementById('staleSelectionHint');
    if (!select || !results || !hint) return;

    var initialValue = select.value;

    select.addEventListener('change', function () {
        var changed = select.value !== initialValue;
        results.classList.toggle('d-none', changed);
        hint.classList.toggle('d-none', !changed);
        if (heading) heading.classList.toggle('d-none', changed);
    });
});


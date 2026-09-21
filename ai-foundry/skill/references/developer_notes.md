# Developer notes

These notes are for human maintainers and future skill-development work only. They are not source material for client report narrative generation. Do not use this file to shape client-facing report interpretation.

## Versioning practice

Use one semantic version for the packaged skill and the report runtime surfaced in generated HTML metadata.

- The single version changes when workflow, scripts, narrative rules, source hierarchy, QA checks, packaged references, report HTML/CSS/JS, fixed report text, rendered visual behavior, or embedded metadata changes.
- Keep the version internal to the HTML source only. Do not put it in the visible report page or report filename.
- Package filenames should include the version, for example `airl-pulse-report_vX.Y.Z.zip`.
- Before packaging any future update, update this file, update `SKILL.md`, update `references/output_contract.md`, and consider whether `references/visual_contracts.md` needs a maintenance-only note.

## Version numbering

Use `MAJOR.MINOR.PATCH`.

- **Major**: substantial redesign, incompatible workbook/schema change, major report structure change, or workflow architecture change.
- **Minor**: new report section, meaningful narrative/QA logic, new data rule, major visual update, new workflow step, or material source-reference expansion.
- **Patch**: typo fixes, small CSS polish, clarification, maintenance-only cleanup, version metadata changes, or non-behavioral refactor.

## Maintenance reminders

- Keep `SKILL.md` as the control plane and put detailed rules in `references/`.
- Keep `narrative_rules.md` focused on generated text behavior.
- Keep `scoring_rules.md` focused on data, scoring, ranking, display, and highlight logic.
- Keep `output_contract.md` focused on report structure, required elements, filename, footer, and internal version metadata.
- Keep `qa_checklist.md` as the final pre-return validation list.

## Skill changelog

### v1.11.17 - Package anonymization hardening
- Removed named-company literals from regression-test fixtures so the reusable skill bundle contains no smoke-test client names or named external-partner examples.
- Kept test intent unchanged by using generic synthetic organization and partner placeholders.
- Added a packaging-time anonymization audit expectation: development smoke reports may use real client workbooks locally, but those reports and client names must never be bundled into the distributable skill.
- Preserved report generation, benchmark logic, narrative behavior, styling, and workbook handling from v1.11.16.


### v1.10.68 - Demographic chart spacing rollback and legend simplification
- Restored Level Distribution bar-column spacing to the prior 128px label column so the label-to-bar gap matches the Year chart rhythm without crowding bars against labels.
- Reverted Region Mix and Assessment Type legends to the simpler inline legend treatment after the compact aligned-percentage variant proved visually fussier in the small cards.
- Preserved the v1.10.66 bar-label typography fix and all v1.10.64 evidence-ledger behavior.
- Updated visual-contract regression coverage for the reverted legend treatment and restored Level Distribution spacing.

### v1.10.67 - Demographic chart spacing and compact legend alignment
- Reduced the Level Distribution label-to-bar gap by moving the bar column left while keeping labels left-aligned.
- Updated Region Mix and Assessment Type legends to align percentages compactly within content-tight legend columns.
- Preserved fixed count columns for bar charts and avoided hover/interactivity changes.
- Added regression coverage for compact pie-legend alignment and the Level Distribution bar-column contract.

### v1.10.66 - Demographic bar-label typography polish
- Increased About-the-Data Volume by Year and Level Distribution row labels and values from 10.5px to 11.5px through the canonical About-the-Data CSS owner.
- Preserved chart card headings at 12px and did not change layout, scoring, narrative, or chart logic.
- Added regression coverage for the demographic bar-label typography contract.

### v1.10.65 - Major CSS source overhaul test

- Rebuilt `assets/report_template.html` stylesheet source formatting for maintainability while preserving cascade order.
- Removed exact duplicate CSS rules by keeping the last identical occurrence to preserve final cascade behavior.
- Reduced template `!important` declarations while avoiding intentional visual design changes.
- Preserved dynamic CSS ownership: Python continues to inject only workbook-driven values.
- Regression harness and smoke render passed; treat v1.10.64 as the clean rollback baseline if visual review identifies unacceptable differences.

### v1.10.64 - External-context evidence ledger support

- Added optional `external_context.vetted_context_bullets` as a structured evidence ledger for specific company external facts, without replacing `ai_strategy_summary` or limiting consultant-style narrative synthesis.
- Added normalization helpers in `scripts/airl_external_sources.py` so URL-backed evidence can come from either `external_context.sources` or vetted bullets.
- Updated validation so AI strategy summaries and high-risk external fact patterns can be grounded by URL-backed sources or complete vetted evidence bullets.
- Rendered vetted-bullet source metadata in the existing External Context Sources section while keeping the factual claims themselves out of the report source list.
- Updated SKILL, web research, narrative, output-contract, and operator-playbook guidance to describe the evidence-ledger pattern as optional factual grounding, not required wording.
- Added regression coverage for valid evidence-ledger rendering, incomplete bullet validation, malformed bullet URLs, and high-risk external fact grounding through vetted bullets.


### v1.10.63 - Stabilization review and visual contract hardening

- Added `references/visual_contracts.md` as a maintenance-only checklist for known fragile visual expectations after CSS, template, or renderer changes.
- Hardened the regression harness so visual polish checks use active CSS selectors and semantic property assertions rather than brittle exact stylesheet fragments where possible.
- Added active-CSS contract coverage for recent regression areas including the Coverage card, data interpretation note, external-source links, AI-Ready Leader CTA, heatmap header alignment, and Follow-up dark-section palette.
- Preserved report output behavior and visual treatment; this release changes regression coverage, maintenance guidance, and version metadata only.

### v1.10.62 - Visual regression repair for dynamic-adjacent CSS comment boundary

- Fixed the dynamic-adjacent static component CSS block in `assets/report_template.html` so its maintenance comment closes before the component selectors. This restores the intended static styles that v1.10.61 moved from Python into the template.
- Restored intended styling for the About-the-Data interpretation-note list rhythm, External Context Sources typography/link treatment, and the AI-Ready Leader Learn More button without changing report data, narrative, chart, heatmap scoring, or section structure.
- Added regression coverage to ensure dynamic-adjacent static CSS selectors remain active and are not accidentally swallowed by template comments.

### v1.10.61 - CSS dead-code and dynamic CSS ownership cleanup

- Removed confirmed unused template CSS for legacy heatmap-note, heat-legend, metric/stat/KPI, section-separator, and old hero-stat class systems that are no longer generated by the report renderer.
- Moved static component CSS that had been injected by `scripts/render_report.py` into `assets/report_template.html`, leaving Python-injected CSS limited to workbook-driven pie gradients and region-legend column values.
- Removed a superseded duplicate demographic/storyline CSS patch layer while preserving the later canonical component rules and current visual values.
- Reduced template CSS cascade debt and `!important` usage without changing report data, narrative, chart, heatmap scoring, section structure, or intended visual design.
- Added regression coverage for the dynamic CSS ownership boundary so static template selectors do not drift back into Python.

### v1.10.60 - Correctness and harness hardening

- Renamed the About-the-Data participant/date card title from `Participant summary` to the shorter single-line `Coverage`.
- Reworded single-row subgroup heatmap copy so it refers to workbook comparison data availability instead of implying the renderer applied an N-size threshold. The minimum subgroup N threshold is enforced upstream in the SQL/export process.
- Removed unused qualifying-subgroup coverage fields from the generated content model and documented that the skill should not duplicate upstream participant-count filtering.
- Added a local missing-responsibility guard in `scripts/build_content_model.py` so missing overall responsibility rows fail with a clear message instead of an opaque numeric conversion error.
- Added `scripts/airl_external_sources.py` to share external-source normalization between validation and rendering, and added malformed/non-http URL validation.
- Removed dead single-row coverage helper code and unused imports, and moved responsibility label variants for linting into `scripts/airl_constants.py`.
- Hardened the regression harness with semantic CSS contract checks and coverage for development render override, malformed URLs, high-risk external facts without sources, all-positive watch-area overstatement, single-row heatmap copy, and missing responsibility rows.
- Aligned SKILL, narrative rules, operator playbook, and output contract wording around the lint → set final → validate/render workflow and the required footer/disclaimer source.

### 1.10.54
- Corrected three typography regressions through existing section-owned CSS selectors rather than late override patches: Region demographic legend labels now inherit the shared demographic pie-legend size, the AI-Ready Leader explainer body copy renders at 16px, and the Benchmark Comparison lead paragraph renders at 16px.
- Preserved report structure, data logic, narrative logic, chart logic, and visual design intent; this release only restores intended body/legend typography sizing.

### 1.10.53
- Added stable AI-operator issue codes and action metadata to content-model validation and narrative lint output so future ChatGPT executions can route fixes by layer instead of treating all failures as generic prose issues.
- Added `references/operator_playbook.md` with concise recovery guidance for `STYLE_*`, `CONTRACT_*`, `SOURCE_*`, `RENDER_*`, and placeholder-related issues.
- Expanded the regression harness from 10 to 11 tests with coverage for issue-code emission, label-led lint routing, and action metadata presence.
- Updated `SKILL.md` to reference the operator playbook and keep workflow guidance focused on entrypoint scripts and action routing, not helper-module implementation details.
- Preserved report output behavior and visual treatment; this release changes AI execution guidance, QA metadata, regression coverage, and version metadata only.

### 1.10.52
- Expanded `scripts/run_regression_tests.py` from 6 to 10 tests to strengthen governance coverage before future validator/linter or CSS work.
- Added edge-case render coverage for all-positive and all-negative responsibility-gap patterns, including benchmark-heading and Relative Strength behavior.
- Added limited-data coverage for zero-row function, level, and region heatmap sections, ensuring deterministic copy renders and heatmap narrative fields are not required.
- Added external-source contract/rendering coverage for missing URL-backed sources, missing source titles, missing purpose notes, source-section rendering, and duplicate URL suppression.
- Added CLI render-gate coverage confirming non-final and placeholder narrative models are blocked in final mode.
- Preserved report output behavior and visual treatment; this release changes regression coverage and version metadata only.

### 1.10.51
- Clarified Focus Area ownership in `scripts/airl_charts.py` by adding explicit Python helpers for selected row indexes, row bounds, and initial pill geometry variables.
- Kept browser JavaScript responsible only for post-layout pill positioning and left selection thresholds, wording, and row classes in Python-owned deterministic logic.
- Strengthened the regression harness with a functional Focus Area contract test covering expected marker rendering, priority row classes, and single-row suppression.
- Preserved report output behavior and visual treatment; this release changes ownership boundaries and regression coverage only.

### 1.10.50
- Replaced remaining layout-oriented inline styles in renderer-produced HTML with named CSS classes for executive signal cards, signal-card ledes, action-section lede text, and fallback action-card titles.
- Preserved data-driven inline styles and CSS custom properties for true variable values such as demographic bar widths, pie colors, heatmap cell colors, and Focus Area geometry.
- Kept the change intentionally no-visual-change: class rules mirror the previous inline declarations and do not alter section markup, layout, typography, colors, or visual behavior.
- Ran the regression harness and smoke render after moving inline presentation styles into template-owned CSS.

### 1.10.49
- Reorganized the `assets/report_template.html` stylesheet comments into structural maintenance sections while preserving selector order for visual parity.
- Removed obsolete historical patch/version comment language from the template CSS without changing CSS declarations, section markup, or report behavior.
- Kept high-risk cascade changes, including broad `!important` reduction and selector reordering, out of this release so the cleanup remains no-visual-change by design.
- Ran the regression harness and smoke render after the CSS source cleanup.

### 1.10.48
- Added `scripts/airl_report_sections.py` for deterministic report-section helpers covering About-the-Data interpretation notes, external source rendering, approximate employee-count formatting, and Korn Ferry logo data-URI loading.
- Removed those helper functions and the embedded logo fallback constant from `scripts/render_report.py` so the renderer continues moving toward assembly-only ownership.
- Preserved report output behavior while reducing renderer-owned non-assembly logic ahead of the CSS/template cleanup phase.
- Ran the regression harness after extraction to confirm full render, limited-data contracts, narrative escaping, final validation checks, and workbook alias normalization still pass.

### 1.10.47
- Added `scripts/airl_default_narratives.py` for development-only placeholder narrative and fallback action-card scaffolding.
- Removed default narrative and fallback recommendation construction from `scripts/render_report.py` so the renderer continues moving toward assembly-only ownership.
- Preserved report output behavior; fallback text remains visibly placeholder-only and client-ready rendering remains gated by `narrative_status = final`.
- Ran the regression harness after extraction to confirm full render, limited-data contracts, narrative escaping, final validation checks, and workbook alias normalization still pass.

### 1.10.46
- Added `scripts/airl_view_model.py` for deterministic display-state helpers between the content model and HTML assembly.
- Moved subgroup heatmap limited/full display decisions, section classes, deterministic limited-data copy, and benchmark heading selection out of `scripts/render_report.py`.
- Preserved report output behavior while continuing the renderer-decomposition path started in 1.10.45.
- Ran the regression harness after extraction to confirm full render, limited-data contracts, narrative escaping, final validation checks, and workbook alias normalization still pass.

### 1.10.45
- Extracted deterministic chart, heatmap, demographic chart, and rank-list HTML helpers from `scripts/render_report.py` into `scripts/airl_charts.py` so the renderer moves closer to assembly-only ownership.
- Added `scripts/airl_render_helpers.py` for shared escaping and numeric display helpers used by chart rendering and report assembly.
- Preserved report output behavior while reducing renderer size and improving separation between deterministic visual fragments and full report assembly.
- Ran the regression harness after extraction to confirm full render, limited-data contracts, narrative escaping, final validation checks, and workbook alias normalization still pass.

### 1.10.44
- Added `scripts/run_regression_tests.py`, a lightweight synthetic regression harness to protect final validation, rendering, narrative escaping, limited-data heatmap contracts, exactly-four follow-up recommendations, signed benchmark-direction checks, placeholder blocking, and workbook responsibility alias normalization before larger renderer/template refactors.
- Added regression coverage as a maintenance-only quality gate with no intended client report visual, scoring, narrative, or workflow behavior change.

### 1.10.43
- Added shared responsibility-name constants so workbook validation and content-model building normalize accepted responsibility aliases consistently.
- Removed hardcoded client-specific short-name exceptions from the content-model builder; short names now use only generic legal-suffix cleanup.
- Escaped LLM-authored narrative strings during HTML rendering so accidental markup cannot break the report shell.
- Made heatmap narrative-field validation conditional on whether comparative heatmap interpretation cards actually render.
- Made development fallback narratives and fallback action cards visibly placeholder-only so they cannot be mistaken for client-ready prose.

### 1.10.42
- Updated limited-data heatmap section headlines for 0-row and 1-row Function, Level, and Region states so they describe the value those cuts can provide without implying unsupported subgroup findings.
- Refined deterministic limited-data body copy for 0-row and 1-row subgroup states and removed the separate bold note title from those inline notes.
- Kept normal comparative heatmap headlines, interpretation cards, and Interpretation Guide behavior unchanged for sections with two or more usable subgroup rows.
- Updated internal HTML metadata to version 1.10.42.

### 1.10.41
- Cleaned Markdown guidance to remove unnecessary LLM instructions for deterministic template/CSS/JS behavior.
- Consolidated output-contract guidance around required sections and behavior while leaving header/navigation mechanics to the renderer/template.
- Reorganized QA into automated gates, manual data/source checks, manual narrative checks, and visual/output checks.
- Split source-capture guidance from source-display behavior and removed stale archival source-doc references.
- Reduced Markdown duplication for Focus Area, external sources, limited-data heatmap states, and hero failure phrases where scripts/template already enforce behavior.
- Updated internal HTML metadata to version 1.10.41 with no intended report visual or narrative behavior change.

### 1.10.40
- Refined unified header motion near the hero boundary.
- Removed the duplicate-accent moment by hiding the hero divider once the sticky header divider is active.
- Nudged sticky-state logo/identity/nav content upward while adding bottom breathing room for nav buttons.
- Preserved opacity-only nav button reveal and current unified header structure.

### 1.10.39
- Cleaned sticky header motion so the logo and identity stay stable while nav buttons reveal with opacity only.
- Reserved nav-link row space from the start and removed height/scale/translate transitions that created an eye-open or bounce effect during slow scrolling.
- Added hysteresis around the nav-button reveal threshold to reduce flicker with mouse-wheel and scrollbar scrolling.

### 1.10.38
- Added spacing between a one-row subgroup heatmap table and its limited-comparison note so the note does not crowd the table.

### 1.10.37
- Refined the unified hero/header layout so the hero headline and subheading use the full report content rail while the full-bleed background and divider remain intact.
- Tightened the spacing between the identity rail and hero headline.
- Made logo alignment state-specific: top-aligned with the identity in the hero state and vertically centered in the sticky nav state.
- Reduced hidden nav-link padding so the initial header/hero gap is not inflated before the nav buttons reveal.

### 1.10.36
- Made the unified hero/header background and hero accent divider full-bleed across the browser while keeping the report body and inner header content centered on the report rail.
- Centered the KF logo within the dark header identity band rather than across the full hero/header height.
- Tightened the header-to-hero headline spacing and kept the single canonical header/nav CSS path after the prior cleanup.


### 1.10.35
- Restored centered report rail after the header cleanup, kept the logo size consistent between initial and sticky states, and tightened the gap between the hero subheading and the bottom of the hero.

### 1.10.34
- Cleaned accumulated legacy sticky-nav/header CSS from the report template so only the canonical unified header behavior remains in the final rendered cascade.
- Removed old dynamic sticky-nav CSS from `render_report.py` so future renders do not reintroduce obsolete header states or override the current behavior.
- Preserved the unified logo/identity header, delayed nav-button reveal, smooth shared hero/header gradient, hero accent divider, and sticky-state accent handoff in one authoritative CSS block.
- Rebuilt the template styling back to a single primary `<style>` block to reduce cascade conflicts and make future header changes visible and maintainable.

### 1.10.33
- Added an authoritative visual override for the unified header after prior header updates were not reliably winning in the rendered CSS cascade.
- Attempted to make the logo visibly larger, vertically center the logo rail, tighten the gap between identity and hero headline, and remove accent fade behavior.

### 1.10.30
- Refined the unified hero/header system so the KF logo and report identity align to the report content rail, reducing the initial gap between the header and hero headline.
- Removed the always-visible accent from the top header state; the gradient accent now appears as the hero divider and becomes the sticky header divider once the header reaches the sticky state.
- Delayed navigation-button reveal until the hero is closer to scrolling out, keeping the top-of-page header calmer and reducing visual clutter.
- Adjusted the header divider/rail spacing so the vertical line supports the logo-to-identity relationship without pushing the header off the report rail.

### 1.10.29
- Reworked the hero and navigation into a unified header system: the KF logo and stacked report identity appear at the top of the hero from page load, the hero uses the same smooth green gradient as the sticky header, and the navigation buttons fade in after scrolling begins instead of appearing as a separate block below the hero.
- Removed the old hero eyebrow and duplicate hero identity treatment so the hero/header behaves as one branded system.
- Preserved sticky active-section navigation, the logo click-to-top behavior, and the shared gradient accent treatment under the hero/header.

### 1.10.28
- Reworked sticky jump navigation to use native sticky positioning in the report flow rather than fixed overlay/body-padding toggling. This removes slow-scroll flicker near the hero boundary, prevents the header from covering the AI-Ready Leader explainer section, and keeps the stacked logo/identity/nav layout, vertical divider, gradient accents, and logo click-to-top behavior.

### 1.10.27
- Corrected sticky nav positioning so the active header is fixed flush to the viewport top with no visible scroll-under gap.
- Preserved active nav content offset so report sections remain readable under the fixed header.

### 1.10.26
- Refined sticky navigation layout to better match the approved mockup: added a vertical divider between the logo and text rail, top-aligned the logo with the stacked identity, aligned the identity with the nav text rather than the active pill edge, and preserved stronger logo proportions.
- Smoothed sticky navigation activation and dismissal by triggering slightly earlier, lengthening the fade/slide transition, and keeping the hero and sticky nav transition cleaner in both scroll directions.
- Reinforced the full-width gradient accent below the hero and the gradient accent under the sticky nav while removing dark divider artifacts.

### 1.10.25
- Tuned the sticky navigation header to better match the stacked mockup design: larger logo, clearer logo/identity/nav proportions, more refined spacing, and nav text aligned on a shared rail.
- Smoothed sticky navigation reveal and hide transitions in both scroll directions using a delayed threshold and longer opacity/transform timing.
- Made the sticky header logo link back to the top/hero of the report.

### 1.10.24
- Refined the sticky navigation into a stacked identity treatment: KF logo at left, AI-Ready Leader Insights and company name stacked on the title rail, and nav pills on a dedicated row.
- Smoothed sticky-nav reveal behavior so the nav appears after the hero clears rather than overlapping the hero during scroll.
- Preserved the full-width gradient hero accent and sticky-nav accent beneath the nav.

### 1.10.23
- Corrected the rendered sticky-navigation and hero-accent CSS so the v1.10.21 design polish is visible in generated reports.
- Enlarged the sticky-nav logo, increased spacing between identity text and nav buttons, aligned identity text with the nav-link rail, and removed the extra dark divider below the nav accent.
- Restored the full-width gradient accent line below the hero using the same gradient treatment as the sticky nav.
- Kept the v1.10.22 narrative-guidance cleanup intact.

### 1.10.22
- Reorganized narrative, output-contract, scoring, and QA guidance so rules are grouped by purpose, source use, narrative element, heatmap behavior, automated gates, and manual QA.
- Removed remaining guidance references to the former heatmap lead-in heading from current instructions, scripts/templates, and historical notes.
- Consolidated Focus Area visual guidance into one canonical output-contract rule, with scoring rules owning selection logic and QA referencing the canonical rule.
- Clarified Interpretation Guide behavior as conditional on two or more usable subgroup rows.
- Verified v1.10.21 sticky navigation, follow-up-card, hero-accent, and benchmark-direction changes remain present in the package, and reinforced hero/sticky-nav accent rules in the output contract.

### 1.10.21
- Restored the required four-card follow-up opportunity layout when narrative generation supplies fewer than four items.
- Removed the redundant heatmap lead-in so heatmap takeaway cards start directly after the table.
- Refined sticky nav spacing with a larger logo, less cramped identity/button spacing, a bottom gradient accent, and no extra dark divider.
- Preserved the gradient accent below the hero and aligned it with the sticky nav accent treatment.
- Added final validation for signed benchmark-direction contradictions such as negative gaps described as above benchmark.
- Updated QA/output contract guidance for four follow-up cards, heatmap takeaway headings, and benchmark-direction consistency.

### 1.10.20
- Set About the Data pie-chart legend text for Regional Mix and Assessment Type to 11.5px for a consistent, slightly lighter legend treatment while keeping overlap-safe vertical legend rows.

### 1.10.19
- Hid the jump navigation while the hero is fully visible so the branded sticky header appears only after the hero scrolls away.
- Reduced sticky-header crowding by tightening logo, identity, pill, and spacing treatment while keeping the compact branded green state.
- Kept the sticky-nav gradient accent below the header and ensured the hero bottom accent uses the same gradient treatment.
- Restored Benchmark Comparison lead paragraph to full report width.
- Set About the Data participant/date captions to 12px and restored the previous Year/Level chart title-to-bar spacing.

### 1.10.18
- Refined sticky navigation header: removed redundant Korn Ferry text from the identity line, aligned logo/identity/navigation into a compact two-row branded header, and moved the gradient accent line beneath the nav.
- Matched the hero bottom accent to the sticky-nav gradient treatment.
- Standardized Regional Mix and Assessment Type legend text sizing.
- Reduced Benchmark Comparison lead paragraph size to align with body paragraph scale.
- Updated report footer brand line to `© 2026 Korn Ferry`.
- Polished Assessment Volume by Year and Level Distribution chart title/body spacing so bars start at the same visual height.

### 1.10.17
- Started from v1.10.16 and applied a focused professional design polish pass.
- Added a compact dark-green sticky navigation state after the hero scrolls away, including a KF logo, stronger identity treatment, and a gradient accent bar while preserving the light nav state near the hero.
- Standardized note/accent borders to a 4px treatment, including the About the Data interpretation note.
- Adjusted the Executive Narrative commercial implication text size to align with the Largest Advantage and Watch Area cards.
- Added breathing room above the participant count in About the Data and refined metric spacing.
- Consolidated skill and report-template version tracking into one internal skill/report version surfaced in HTML metadata.

### 1.10.16
- Tightened hero subheading narrative rules and validation to block `directional` and related methodology/report-description phrasing in hero copy while preserving those terms for About the Data and limited-data notes.
- Updated hero-subheading lint and content-model validation so the hero states the client implication directly rather than describing the report/evidence.
- Includes report template `1.7.14`.

### 1.10.15
- Started from v1.10.14 and tightened executive-summary narrative grounding so positive-content checks encourage one concise data or benchmark anchor without allowing number-heavy executive paragraphs.
- Updated narrative guidance to lead the executive narrative with implication, avoid participant-count anchors, and save detailed score evidence for visible cards, tables, and heatmaps.
- Strengthened `scripts/validate_content_model.py` so final narrative validation flags executive summaries with more than one quantitative anchor or participant-count anchoring.
- Includes report template `1.7.14`.

### 1.10.14
- Started from v1.10.13 and added enforceable final-narrative/content-model quality gates.
- Added `scripts/validate_content_model.py` and made `scripts/render_report.py` block client-ready rendering unless `narrative_status` is `final`, with `--allow-default-narrative` reserved for development testing.
- Expanded narrative linting to include positive-content checks for client-specific substance, AI/Human + AI relevance, data/benchmark anchoring, action language, source-grounding requirements, and high-risk external fact patterns.
- Added deterministic `Largest Advantage` versus `Relative Strength` labeling based on whether the highest responsibility gap is positive, plus watch-area framing metadata for all-positive patterns.
- Strengthened workbook validation for required legal client metadata, required six Overall/Composite responsibilities, numeric ranges, duplicate aggregate rows, and gap consistency warnings.
- Includes report template `1.7.14`.

### 1.10.13
- Started from v1.10.12 and standardized the bottom External context sources display.
- Renders each external source as a linked source/headline plus concise inline purpose/context note.
- Keeps URLs mandatory as link targets but does not print raw URL strings underneath sources.
- Includes report template `1.7.13`.

### 1.10.12
- Started from v1.10.11 and applied targeted polish/QA updates.
- External context sources now require URL-backed entries and render each visible URL in the bottom source-reference section while keeping URLs out of narrative boxes.
- Refined the About the Data participant card spacing and set note/accent border width to the same 4px treatment used by storyline-style notes.
- Tightened hero subheading narrative/lint rules to prevent report/readout/sample self-description such as `This directional readout...`.
- Includes report template `1.7.12`.

### 1.10.11
- Started from v1.10.10 and applied only targeted visual polish requested after review.
- Restored the Function heatmap `Focus Area` pill by ensuring function sections carry the `functional-heat` class used by the existing CSS/JS positioning logic.
- Refined the participant-count card to lead with the participant total and align the participant/date metrics cleanly without a redundant card title.
- Removed the redundant green-accented heatmap lead-in and standardized left-accent widths across note/card treatments.
- Includes report template `1.7.11`.

### 1.10.10
- Started from accepted v1.10.8 baseline after v1.10.9 was not retained.
- Changes only the approved subset: sticky-nav identity text size, explainer button text, participant count card formatting, Year/Level chart spacing, and executive-summary narrative/lint guardrails for vague strategy-context self-references.
- Includes report template `1.7.10`.

### 1.10.8
- Simplified the front-of-report explainer layout so the title and button sit in the section header and the approved copy sits directly in the standard report card without a nested content box.
- Rounded and shadowed the About the Data interpretation note to match other report note styles.
- Corrected Assessment Volume by Year and Level Distribution alignment so demographic bar charts start at the top under their titles.
- Includes report template `1.7.8`.

### 1.10.7
- Simplified the front-of-report `What is the AI-Ready Leader?` explainer from a shaded/nested treatment into one standard report-style card.
- Kept the approved explainer text and public article button, with full-width copy and the button consistently beneath the text.
- Includes report template `1.7.7`.

### 1.10.6
- Added a compact front-of-report `What is the AI-Ready Leader?` explainer section between sticky navigation and About the Data.
- Added a `Learn more about the AI-Ready Leader` button linking to the public Korn Ferry Institute article without placing raw URLs in narrative text.
- Kept the explainer focused on the Success Profile concept and avoided repeating the six responsibility names already used elsewhere in the report.
- Includes report template `1.7.6`.

### 1.10.5
- Expanded limited-data subgroup coverage notes to use the full section width for cleaner 0-row and 1-row Function, Level, and Region states.
- Added a compact bottom `External context sources` section for linked source attribution supporting employee count and AI/digital context, while keeping raw URLs out of narrative boxes.
- Added narrative guidance for light, company/industry-grounded AI context and a lint guardrail against report refresh/version self-references such as `updated report` or `fresh read`.
- Includes report template `1.7.5`.

### 1.10.4
- Refined limited-comparison coverage-note formatting so the heading remains separate and the note body renders as one continuous paragraph with the subgroup name inline.
- Preserved the one-row subgroup heatmap behavior and all limited-data logic introduced in 1.10.3.
- Includes report template `1.7.4`.

### 1.10.3
- Added deterministic one-row subgroup rendering for Function, Level, and Region sections: keep the single-row heatmap visible but replace normal comparative takeaways and Interpretation Guide with one limited-comparison note.
- Generalized the limited subgroup logic so 0 usable subgroup rows show one coverage note, 1 usable row shows a single-row heatmap plus one caution note, and 2+ usable rows use the normal comparative heatmap narrative.
- Includes report template `1.7.3`.

### 1.10.2
- Polished report rail alignment so hero content, sticky navigation, and report sections align more consistently.
- Refined About the Data responsive behavior to use medium-width wrapping before single-column stacking, top-align year and level bar charts, and keep Assessment Type legend entries on separate rows to prevent overlap.
- Added deterministic limited-data rendering for missing function, level, or region subgroup score rows: sections remain visible with one workbook-driven coverage note and no empty heatmap table or generic takeaways.
- Includes report template `1.7.2`.

### 1.10.1
- Refined the sticky jump navigation so the report identity uses a smaller one-line treatment above the pills and reveals only after the hero has mostly scrolled away.
- Renamed the About the Data nav pill to `Data` and kept the nav pills on their own full-width row to prevent crowding.
- Includes report template `1.7.1`.

### 1.10.0
- Added a sticky report identity and jump navigation bar directly below the hero, with `Korn Ferry AI-Ready Leader Insights | [Company Name]` identity text, section pill links, active-state scroll sync, and narrow-screen horizontal scrolling.
- Added section IDs and scroll-margin behavior for reliable jump-link navigation.
- Hid the jump navigation in print and intentionally did not add section dimming or blur so client reports remain readable while scrolling.
- Includes report template `1.7.0`.

### 1.9.1
- Updated About the Data demographic cards to stack vertically in narrower browser windows before chart labels or legends can overflow.
- Preserved desktop demographics layout and all data, scoring, narrative, and template content unrelated to responsive card behavior.
- Includes report template `1.6.10`.

### 1.9.0
- Added optional `ClientName` support for displaying alphabetized distinct Korn Ferry client record names in the About the Data interpretation note.
- Refactored the Data interpretation note into a concise bullet list with client coverage, method, interpretive caution, and participant-count guidance.
- Added standard guidance that Korn Ferry recommends at least 100 participants for interpretation.
- Preserved parent-company and short-name behavior everywhere else in the report.
- Includes report template `1.6.9`.

### 1.8.1
- Updated heatmap shading to use a balanced absolute red-gray-green scale based on each cell's rounded displayed gap value.
- Added stronger red gradations for larger negative gaps and converted the positive side to a single green ramp instead of mixed teal/green shades.
- Preserved true neutral shading for rounded zero values, including small negative values that round to `0`.
- Includes report template `1.6.8`.

### 1.8.0
- Added support for a dedicated `DataType = Overall` row as the authoritative source for the Benchmark Comparison `[Client] Overall` bar.
- Preserved the historical composite-average fallback for older workbooks that do not include `DataType = Overall`.
- Updated workbook validation and scoring/schema guidance for the new overall-row data rule.
- Includes report template `1.6.7`.

### 1.7.8
- Sorted Year demographic chart records chronologically by year.
- Sorted Level demographic chart records using the standard hierarchy: Executive, Senior Leader, Mid Level Manager, Front Line Manager, Individual Contributor.
- Removed client-specific wording from the report template human-review comment.
- Placed Benchmark first in the Benchmark Comparison legend so long client names do not overlap the Benchmark label.
- Includes report template `1.6.7`.

### 1.7.6
- Removed an invalid nested `<style>` opener from the report template without changing visual behavior.
- Added human-review comments in `scripts/render_report.py` around the latest maintenance-sensitive rendering logic.
- Includes report template `1.6.6`.

### 1.7.5
- Restored compact-but-aligned starts for Underlying Leadership Signal lists and Recommended Follow-up Opportunity body text without reintroducing large fixed gaps.
- Added hero subtitle lint checks to block sample/report-description lead-ins such as participant counts, `assessed leaders`, `This early-read signal draws on`, and `The results describe`.
- Includes report template `1.6.5`.

### 1.7.4
- Shifted Benchmark Comparison text labels slightly right to reduce the text-to-bar gap without changing bar geometry or card size.
- Reduced Executive Narrative left-column text width to create cleaner separation from advantage/watch cards.
- Includes report template `1.6.4`.

### 1.7.3
- Reverted Benchmark Comparison bar geometry to the accepted row-centered alignment while retaining the client-specific overall label and score-reading footnote.
- Removed excess spacing introduced in Underlying Leadership Signals and Recommended Follow-up Opportunity cards.
- Removed repeated client name from the employee-count phrase in the About the Data interpretation note.
- Refined Executive Narrative right-card top alignment.
- Includes report template `1.6.3`.

### 1.7.2
- Tightened hero subtitle guardrails to block report-description and sample-description lead-ins.
- Added targeted visual template patch for Executive Narrative card alignment, Benchmark Comparison spacing/footnote, Underlying Leadership Signals table alignment, and Recommended Follow-up card text alignment.
- Includes report template `1.6.2`.

### 1.7.1
- Adopted `MAJOR.MINOR.PATCH` versioning convention.
- Consolidated skill and template changelogs into this maintenance-only developer notes file.
- Updated package naming convention to include skill version.
- Updated report template internal metadata to template version `1.6.1` with no visual behavior change.

### 1.7.0
- Added skill and template version-control guidance.
- Added measurement-boundary guardrails: scores indicate leadership readiness signals, not proof of AI initiative success or operational performance.
- Added functional strategy relevance guidance for interpreting functional patterns against client AI/digital strategy.
- Retained mandatory narrative label lint and counter-pattern safeguards.
- Included report template `1.6.0`.

### 1.6.0
- Added mandatory narrative label linting workflow and `scripts/lint_narrative_labels.py`.
- Strengthened no-label-list rules for narrative prose.
- Added counter-pattern guidance as optional nuance and an overgeneralization safeguard.

### 1.5.0
- Cleaned and reorganized narrative rules to separate overall guidance from section/element-specific guidance.
- Tightened source-reference usage rules and anti-label guidance.
- Added recent-source employee count selection guidance.

### 1.4.0
- Added insight spine guidance to improve internal coherence and repeat-run consistency without forcing generic language.
- Added QA checks for coherent storyline across sections.

### 1.3.0
- Converted major AI-Ready Leader source materials into curated Markdown references.
- Added construct/composite definitions as LLM-readable behavioral interpretation source.
- Clarified source hierarchy and archival role of original source documents.

### 1.2.0
- Added narrative quality standards, section-level prompts, required callouts, and stronger anti-overclaiming guardrails.
- Added stricter Custom GPT/flat Knowledge guidance.

### 1.1.0
- Added workbook validation, content-model generation, HTML rendering workflow, source context rules, and QA checklist.
- Added logo fallback and client legal-name handling.

### 1.0.0
- Established AIRL Pulse Report skill from the v1.0 report template base.
- Defined core workflow for generating HTML reports from client workbooks.

### Pre-1.0 development milestones
- **0.9.x**: Assembled early skill structure, workbook schema assumptions, report-generation workflow, and Custom GPT guidance.
- **0.8.x**: Added source-reference handling, first narrative rules, and early QA/output contract concepts.
- **0.7.9**: Legacy development report used as visual and narrative prototype for the eventual stable template base. This prototype is not source material for future client narratives.

## Report template changelog

### 1.7.13 - Historical template changelog
- Standardizes bottom External context sources display with linked titles and inline source-purpose notes, without visible raw URL strings.

### 1.7.12
- Displays visible URLs in the bottom External context sources section, refines participant/date metric spacing, and keeps note/card accent widths at the standardized 4px treatment.

### 1.7.11
- Restores the Function heatmap Focus Area pill, refines the participant/date card formatting, removes the redundant heatmap lead-in accent, and standardizes left-accent widths across report notes/cards.

### 1.7.10
- Started from accepted template 1.7.8 baseline after template 1.7.9 was not retained.
- Applies only the approved visual polish: `Learn More` button label, larger sticky identity, inline participant total label, and added spacing under Year/Level demographic chart titles.

### 1.7.8
- Moved the AI-Ready Leader explainer button into the title row, removed the nested explainer-card visual treatment, rounded the data interpretation note, and top-aligned the demographic bar charts.

### 1.7.7
- Simplified the AI-Ready Leader explainer styling to a single full-width card, removed the shaded section background, and placed the button below the text.

### 1.7.6
- Added the fixed AI-Ready Leader explainer card and public article button below the sticky navigation.
- Updated required section order and QA expectations for the explainer.

### 1.7.5
- Expanded limited-data coverage notes to full section width so 0-row and 1-row subgroup states do not leave empty card-grid space.
- Added compact bottom External context sources styling for linked company context references.

### 1.7.4
- Refined limited-comparison note formatting so inline subgroup names no longer inherit title block styling.

### 1.7.3
- Added single-row subgroup heatmap handling for Function, Level, and Region sections, preserving visible data while suppressing comparative cards when no comparison is supported.

### 1.7.2
- Polished shared rail alignment across hero, sticky jump navigation, and report sections.
- Adjusted About the Data demographic cards to wrap at medium widths before fully stacking, top-align year and level bar charts, and render Assessment Type legend items as separate rows.
- Added limited-data coverage-note rendering for subgroup sections when no heatmap rows are available, including region-specific copy based on workbook demographics.

### 1.7.1
- Refined sticky jump navigation identity behavior: the one-line identity is hidden while the hero is visible, revealed after the hero has mostly scrolled away, and displayed above the pill row to avoid layout clashes.
- Renamed the About the Data jump link to `Data`.

### 1.7.0
- Added sticky report identity and section jump navigation below the hero, with active-section highlighting, horizontally scrollable pill links, and print-safe behavior.
- Added stable section anchor IDs and scroll offsets.
- Preserved the non-sticky hero and did not implement report-wide dimming/blur.

### 1.6.10
- Added responsive CSS for About the Data demographic cards so narrow browser windows use a clean single-column card layout and keep labels, legends, and chart contents inside each card.

### 1.6.9
- Converted the About the Data interpretation note from a paragraph to a bullet list.
- Added optional display of Korn Ferry client record names and participant-count interpretation guidance.

### 1.6.8
- Updated heatmap color behavior to a balanced absolute diverging scale with warm red-gray, true neutral, and cool green-gray center bands.
- Heatmap colors are now assigned from the rounded displayed gap value so rounded zero remains true neutral.

### 1.6.7
- Sorted demographic chart records deterministically for Year and Level displays.
- Removed client-specific wording from the report template human-review comment.
- Reordered the Benchmark Comparison legend so Benchmark appears before the client result label.

### 1.6.6
- Removed an invalid nested `<style>` opener from the top template CSS block.
- No intended visual behavior change from `1.6.5`.

### 1.6.5
- Restored compact alignment behavior for Underlying Leadership Signals and Recommended Follow-up Opportunity card body starts.
- Preserved benchmark bar geometry and existing card sizing.

### 1.6.4
- Shifted Benchmark Comparison text labels slightly right while preserving bar geometry and card size.
- Reduced Executive Narrative left-column max width for cleaner spacing to the adjacent cards.

### 1.6.3
- Reverted benchmark SVG bar vertical geometry to the accepted centered alignment.
- Removed extra min-height spacing in Underlying Leadership Signals and Recommended Follow-up Opportunity cards.
- Adjusted Executive Narrative card margin and preserved benchmark footnote additions.

### 1.6.2
- Adjusted Executive Narrative card alignment.
- Updated Benchmark Comparison row label, bar alignment, spacing, and score-reading footnote.
- Updated Underlying Leadership Signals score-reading footnote wording and table alignment.
- Standardized Recommended Follow-up Opportunity body text alignment.

### 1.6.1
- Converted internal template metadata to semantic version format.
- No visual behavior change from `1.6.0`.

### 1.6.0
- Current stable visual version with Focus Area pill micro-adjustment.
- Maintains internal HTML template version metadata only.
- Retains full-width heatmap layout and stable About the Data card alignment from the accepted visual baseline.

### 1.5.0
- Added functional Focus Area visual treatment and smarter functional highlight logic.
- Updated section-heading emerald divider placement.
- Refined heatmap highlight styling.

### 1.4.0
- Embedded Korn Ferry logo fallback and hero legal-name tag behavior.
- Updated hero metadata usage and required footer/disclaimer behavior.

### 1.3.0
- Added and standardized Interpretive Storyline, heatmap callouts, and required narrative boxes.
- Strengthened required section ordering and output contract behavior.

### 1.2.0
- Added expanded About the Data and demographic visual elements.
- Added benchmark and leadership signal display refinements.

### 1.1.0
- Applied KF Beautiful-aligned styling refinements and HTML-only output packaging conventions.

### 1.0.0
- Established first stable AIRL Pulse Report template base from the v0.79 development report.

### Pre-1.0 development milestones
- **0.9.x**: Drafted template sections, report flow, and initial client-ready narrative placement.
- **0.8.x**: Added early KF-inspired styling, chart/heatmap treatments, and visual hierarchy experiments.
- **0.7.9**: Development prototype used as visual reference for the stable v1.0 template base.


### v1.10.56 - Component CSS consolidation

- Consolidated component-level CSS for the AIRL explainer, About-the-Data demographic cards, Benchmark Comparison, Executive Summary cards, Interpretive Storyline cards, and Recommended Follow-up Opportunities into a canonical post-dynamic component section.
- Removed superseded pre-dynamic About-the-Data density/rail rules and duplicated executive-card rhythm rules while preserving current visual values.
- Moved action-grid and action-title/lede styling out of the hero/nav ownership area so component presentation is not mixed with header behavior.
- Kept hero/nav, global token changes, dynamic workbook-driven values, and global `!important` reduction out of scope.
- No report data, narrative, heatmap, chart logic, or intended visual design changes.

### v1.10.57 - Header CSS risk audit and targeted cleanup

- Audited remaining template CSS duplication and confirmed the highest-risk residual area is hero/header/sticky navigation behavior.
- Removed obsolete pre-canonical hero/header patch layers that were superseded by the canonical full-bleed hero and sticky jump-nav section.
- Removed unused legacy header-demographic/brand-logo fragments tied to the old hero-grid header pattern.
- Added a maintenance note marking the canonical hero/header/nav CSS block as the active owner for header, logo/navigation rail, sticky jump-nav, and responsive header behavior.
- Kept the active canonical hero/nav selectors, sticky behavior, dynamic workbook-driven values, and global `!important` cleanup otherwise out of scope.
- No report data, narrative, heatmap, chart logic, report structure, or intended visual design changes.

### v1.10.59 - CSS regression repair for demographics and follow-up actions

- Repaired visual regressions introduced during CSS consolidation in the About-the-Data participant summary card and Recommended Follow-up Opportunities section.
- Restored participant/date metric rhythm in the participant summary card through the canonical About-the-Data CSS owner, with shared dark metric color, restored date metric size, and clearer spacing between date rows.
- Restored dark-section typography and action-card contrast in Recommended Follow-up Opportunities through scoped `section.actions` rules, including light-mint kicker text, soft mint body copy, white card titles, and translucent action-card panels.
- Kept the repair scoped to existing section-owned CSS; no data, narrative, chart, heatmap logic, report structure, or intended design change beyond regression restoration.




## 1.11.9

- Restored responsive About-the-Data demographic-card reflow after the fixed five-column desktop grid began persisting at narrow viewport widths.
- Added a two-column medium-width layout with Level Distribution spanning the row, followed by a one-column narrow-width layout.
- Preserved canonical card order and desktop presentation.
- Added regression coverage for the responsive demographic layout contract.

## 1.11.8

- Restored the Underlying Leadership Signals score-reading note as fixed, benchmark-independent copy rather than client- or benchmark-injected text.
- Added a section-owned `signals-score-footnote` class and restored compact 12px typography with 1.4 line-height.
- Added regression coverage for the fixed note text and typography contract.

## 1.11.7

- Corrected the inline benchmark control's vertical rhythm so the centers of the Overall/Stretch buttons align exactly with the centers of the section-navigation pills.
- Positioned the compact `Benchmark` label independently above the segmented track so it no longer pushes the benchmark buttons downward.
- Preserved the v1.11.6 content-rail inset, slightly smaller benchmark buttons, responsive reflow behavior, and standalone nav-pill treatment.

## 1.11.6

- Replaced the floating benchmark selector with a refined inline sticky-navigation control based on the v1.11.4 visual direction.
- Kept benchmark buttons slightly smaller than section-navigation pills while centering both control groups to the same navigation-row rhythm.
- Tightened section-link spacing and inset the benchmark selector so its right edge aligns with the report content rail rather than the browser edge.
- Preserved the original standalone nav-pill treatment; no recessed background was added behind section navigation.
- Added responsive behavior that uses horizontal link scrolling at medium widths and moves the benchmark control to a clean lower row when space is constrained.

## 1.11.5

- Moved the dual-benchmark control out of the sticky header into a floating viewport control.
- Positioned the control just outside the report rail when wide-screen space allows, with a compact bottom-right overlay fallback on narrower windows.
- Preserved delayed visibility so the control appears only when sticky section navigation is active.
- Improved short-window navigation behavior with progressive logo sizing, tighter pill spacing, controlled wrapping, and a compact horizontal-scroll layout on small screens.
- Hid the floating control in print output so only the active benchmark view is printed.

## 1.11.4

- Refined the sticky-header benchmark control while keeping the `Benchmark` label above the Overall/Stretch buttons.
- Increased the benchmark label slightly to 10px for clearer hierarchy.
- Spanned the control across the header rows so the segmented buttons visually compose with the section-navigation row while the label remains above.
- Matched the benchmark button control height to the 28px section-navigation pills and added deliberate horizontal separation between navigation and benchmark controls.
- Preserved the distinct mint benchmark active state, sticky-only visibility, content-rail alignment, and responsive fallback.

## 1.11.3

- Refined the sticky-header benchmark control into a compact two-line unit with `Benchmark` centered above the Overall/Stretch segmented buttons.
- Aligned the control to the report-content rail without changing sticky behavior.
- Reduced section-navigation pill height slightly and replaced the stark-white active state with a softer pale-mint treatment.
- Preserved a stronger mint active state for the benchmark toggle so benchmark selection remains visually distinct from section navigation.

## 1.11.2

- Polished the sticky benchmark comparison control without changing toggle behavior or navigation height.
- Changed the control label from `Compare to` to `Benchmark comparison`.
- Moved only the two benchmark buttons into the recessed segmented-control track, leaving the label outside the sunken area.
- Changed the active benchmark button to the established light-mint treatment so it is visually distinct from active navigation pills.
- Preserved the existing rule that the control appears only after the sticky section navigation is visible.

## 1.11.1

- Promoted the stabilized dual-benchmark capability to a minor-version release because it expands workbook schema support, content-model structure, rendering behavior, sticky navigation, narrative workflow, validation, and regression coverage.
- Moved the dual-benchmark toggle into the upper-right title row of the sticky navigation so it does not increase desktop nav height.
- Removed repeated active-benchmark badges from report sections.
- Restored benchmark and heatmap footnotes to the static v1.10.68 wording and preserved their established typography.
- Kept Recommended Follow-up Opportunities shared across benchmark views.
- Repaired functional Focus Area pill positioning for benchmark toggles by recalculating after the visible benchmark panel is laid out.




## 1.11.16

- Corrected the Benchmark Comparison overall-row definition to describe the database-provided aggregate result rather than an average across six responsibilities.
- Increased the sticky benchmark selector label and button text to 12px to match section-navigation text while preserving the smaller benchmark button geometry.
- Updated visual-contract guidance for benchmark selector typography.

## 1.11.15

- Refactored sticky header responsiveness into explicit layout zones: flexible section navigation plus a fixed right-hand benchmark control aligned to the report rail.
- Reduced unnecessary desktop nav spacing and removed benchmark-side inset that consumed usable width.
- Added a medium-width structural reflow where the nav spans the full lower row while logo/title remain stable above it, preventing premature nav shrinkage and logo/title collisions.
- Added a narrower breakpoint that moves the benchmark control to its own row only when needed, while allowing section navigation to wrap cleanly.
- No report data, scoring, narrative, benchmark, or section-content behavior changed.

## 1.11.14
- Fixed coordinated sticky-header responsive behavior so the High Engagement benchmark control reflows before competing with the Follow-up navigation item.
- Section navigation now wraps into additional rows at constrained widths instead of remaining rigid or relying on hidden horizontal overflow.
- Preserved benchmark toggle styling, benchmark logic, report content, and narrative behavior.

## 1.11.13

- Repaired sticky-navigation responsiveness for the longer `High Engagement` toggle label by compressing the desktop rail earlier and reflowing the benchmark control before clipping.
- Updated the static About-the-Data interpretation note to recognize the selected Overall or High Engagement benchmark.
- Expanded the selected High Engagement Benchmark Comparison footnote with a concise aspirational-comparison rationale while retaining the Work Engagement job-performance-proxy explanation.
- Hardened Structure and Balance interpretation as low-target constructs in the AIRL profile; stronger profile fit reflects lower need for the named construct, not more of it.
- Added narrative lint coverage for literal reversed interpretations such as `high Structure`, `more Structure`, `enough Structure`, and `high Balance`.

## 1.11.12

- Folded benchmark population/methodology context into the existing Benchmark Comparison `How to read the scores` footnote.
- Each benchmark view now shows only its own deterministic context while selected; removed the separate two-benchmark context card and its CSS.
- Kept benchmark methodology copy configuration-driven through `references/benchmark_definitions.json`.

## 1.11.11

- Branched from v1.11.9; v1.11.10 was an experimental visual-theme prototype and is not the basis for this release.
- Replaced the provisional Stretch benchmark naming with the deterministic **High Engagement Benchmark**.
- Added `references/benchmark_definitions.json`, converted from the approved top-quartile Work Engagement benchmark workbook, as the canonical source for fixed High Engagement Overall, responsibility, and construct values.
- Updated content-model construction to apply the same fixed measurement-grain benchmark across Overall, Function, Level, and Region rows and calculate `GapVsBenchmark2` in Python. Legacy workbook second-benchmark columns are accepted but overwritten by the canonical reference.
- Added deterministic Benchmark Context content to Benchmark Comparison with approximate participant/organization scale for both benchmarks and the Work Engagement methodology note.
- Tightened dual-benchmark narrative guidance so each view tells a standalone leadership story and avoids legacy `stretch`, `higher bar`, and `aspiration gap` framing. Added lint coverage for those patterns in High Engagement narrative fields.
- Expanded regression coverage for fixed-benchmark lookup, benchmark gap calculation, context rendering, and benchmark-framing lint behavior.

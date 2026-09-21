#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

from airl_benchmarks import benchmark_by_id, default_benchmark_id, model_for_benchmark, narrative_for_benchmark
from airl_charts import bars, chart, conic, function_heat_html, heat_table, rank_list
from airl_render_helpers import esc, gap, safe_narratives
from airl_default_narratives import action_cards, default_narratives
from airl_view_model import benchmark_title, render_heatmap_section
from airl_report_sections import data_interpretation_note, external_sources_section, format_employee_count, load_kf_logo_src


def benchmark_toggle(benchmarks):
    if len(benchmarks) <= 1:
        return ""
    buttons = []
    for benchmark in benchmarks:
        bid = esc(benchmark.get("id", ""))
        label = esc(benchmark.get("short_label") or benchmark.get("label") or bid)
        active = " active" if benchmark.get("is_default") else ""
        pressed = "true" if benchmark.get("is_default") else "false"
        buttons.append(f'<button type="button" class="benchmark-toggle-button{active}" data-benchmark-toggle="{bid}" aria-pressed="{pressed}">{label}</button>')
    return f'<div class="benchmark-toggle"><span class="benchmark-toggle-label">Benchmark</span><div class="benchmark-toggle-track" role="group" aria-label="Benchmark comparison view">{"".join(buttons)}</div></div>'



def view_attrs(benchmark, default_id):
    bid = esc(benchmark.get("id", ""))
    hidden = "" if benchmark.get("id") == default_id else " hidden"
    return f'data-benchmark-view="{bid}"{hidden}'


def narrative_for_view(base_model, view_model, benchmark_id):
    n = default_narratives(view_model)
    n.update(narrative_for_benchmark(base_model, benchmark_id))
    return safe_narratives(n)


def executive_section(view_model, n, client):
    m = view_model["metrics"]
    largest = m["largest_advantage"]
    watch = m["watch_area"]
    largest_label = m.get("largest_advantage_label") or ("Largest Advantage" if float(largest.get("gap_vs_benchmark", 0)) > 0 else "Relative Strength")
    return f'''<section class="split executive-section"><div><div class="section-kicker">Executive narrative</div><h2>{n['executive_h2']}</h2><p class="lede">{n['executive_p1']}</p><p>{n['executive_p2']}</p><div class="callout"><b>Commercial Implication:</b> {n['commercial_implication']}</div></div><div class="cards executive-signal-cards"><div class="card"><div class="num">{gap(largest['gap_vs_benchmark'])}</div><h3>{esc(largest_label)}: {esc(largest['display'])}</h3><p>{n['largest_narrative']}</p></div><div class="card"><div class="num">{gap(watch['gap_vs_benchmark'])}</div><h3>Watch Area: {esc(watch['display'])}</h3><p>{n['watch_narrative']}</p></div></div></section>'''


def storyline_section(n, benchmark):
    return f'''<section class="storyline-top"><div class="section-kicker">Interpretive storyline</div><h2>{n['story_h2']}</h2><div class="insight-grid"><div class="impact-card"><h3>{n['story_card_1_title']}</h3><p>{n['story_card_1_text']}</p></div><div class="impact-card"><h3>{n['story_card_2_title']}</h3><p>{n['story_card_2_text']}</p></div></div><div class="accordion-grid"><div class="storyline-row" data-row-sync><details class="insight-toggle"><summary>{n['story_toggle_1_title']}</summary><p>{n['story_toggle_1_text']}</p></details><details class="insight-toggle"><summary>{n['story_toggle_2_title']}</summary><p>{n['story_toggle_2_text']}</p></details></div><div class="storyline-row" data-row-sync><details class="insight-toggle"><summary>{n['story_toggle_3_title']}</summary><p>{n['story_toggle_3_text']}</p></details><details class="insight-toggle"><summary>{n['story_toggle_4_title']}</summary><p>{n['story_toggle_4_text']}</p></details></div></div></section>'''


def benchmark_section(view_model, client, benchmark):
    m = view_model["metrics"]
    context = str(benchmark.get("footnote_context") or "").strip()
    context_html = f" {esc(context)}" if context else ""
    return f'''<section class="panel benchmark-section"><div class="section-kicker">Benchmark comparison</div><h2>{esc(benchmark_title(client, m['average_gap_vs_benchmark']))}</h2><p class="lede">The benchmark pattern should be read as a leadership deployment signal: stronger gaps show where readiness may already be usable for AI activation, while lower gaps show where enablement may be needed to protect sustained value creation.</p><div class="chart-wrap">{chart(view_model)}</div><p class="gap-footnote benchmark-score-footnote"><b>How to read the scores:</b> The results shown indicate the percentage of assessed competencies, traits, and drivers that meet or exceed the AI-Ready Leader Success Profile target score.{context_html}</p></section>'''


def signals_section(view_model, n, client):
    m = view_model["metrics"]
    return f'''<section class="underlying-signal-section"><div class="section-kicker">Underlying leadership signals</div><h2>The construct-level pattern shows where AI-ready leadership behaviors are strongest and where they are more constrained.</h2><div class="two-col"><div class="list-card"><h3 class="signal-card-title-inverse">Highest Differentiators vs Benchmark</h3><p class="lede signal-card-lede-inverse">{n['signals_high_text']}</p><ul class="rank-list">{rank_list(m.get('top_constructs', []))}</ul></div><div class="list-card light"><h3>Relative Watchpoints</h3><p class="lede signal-card-lede">{n['signals_low_text']}</p><ul class="rank-list">{rank_list(m.get('watchpoint_constructs', []))}</ul></div></div><p class="gap-footnote signals-score-footnote"><b>How to read the scores:</b> Gap values are percentage-point differences between client scores and the selected benchmark. Positive values indicate scores above the benchmark; larger values indicate a stronger relative advantage.</p></section>'''


def heatmap_sections(view_model, n, client, suffix=""):
    suffix = f"-{suffix}" if suffix else ""
    return "\n".join([
        render_heatmap_section(f"functional-patterns{suffix}", "Functional patterns", "Functional results show where AI-readiness should be accelerated or enabled.", "function", view_model, n, client, function_heat_html(view_model), "Use functions with larger gaps above the benchmark as acceleration zones. Use functions below the benchmark as enablement priorities before asking them to carry enterprise-wide AI transformation. Small n sizes should be used directionally, not as definitive population comparisons."),
        render_heatmap_section(f"population-patterns{suffix}", "Job Level patterns", "Readiness advantage varies by leadership layer.", "level", view_model, n, client, heat_table(view_model['heatmaps']['level'], 0), "Review job-level results as a deployment guide. Leadership levels with larger gaps above the benchmark can be used as activation points for role-based adoption. Levels below the benchmark may need clearer context, workflow support, and manager enablement before being expected to model AI-native behaviors at scale. Small n sizes should be used directionally, not as definitive population comparisons."),
        render_heatmap_section(f"regional-patterns{suffix}", "Regional patterns", "Regional results show where readiness is strongest and where enablement may be needed.", "region", view_model, n, client, heat_table(view_model['heatmaps']['region'], 0), "Review regional results as a deployment guide. Regions with larger gaps above the benchmark can serve as acceleration zones for testing, learning, and transferring practices across markets. Regions below the benchmark may require more focused enablement before scaling enterprise expectations. Small n sizes should be used directionally, not as definitive population comparisons."),
    ])


def actions_section(view_model, n):
    return f'''<section id="follow-up-opportunities" class="actions"><div class="section-kicker">Recommended follow-up opportunities</div><h2>Turn readiness into enterprise AI value.</h2><p class="lede actions-lede">Use the assessment pattern to convert AI ambition into targeted leader deployment, enablement and follow-up conversations.</p><div class="action-grid">{action_cards(view_model, n)}</div></section>'''


def benchmark_variant_stack(section_id, variants):
    return f'<div id="{section_id}" class="benchmark-view-stack">{"".join(variants)}</div>'


def render(model):
    skill_root = Path(__file__).resolve().parents[1]
    logo_src = load_kf_logo_src(skill_root)
    c = model["client"]["short_name"]
    legal = model["client"]["legal_name"]
    d = model["demographics"]
    benchmarks = model.get("benchmarks") or [benchmark_by_id(model)]
    default_id = default_benchmark_id(model)
    default_view = model_for_benchmark(model, default_id)
    default_n = narrative_for_view(model, default_view, default_id)

    rgrad, rleg, rtip = conic(d["region_distribution"])
    tgrad, tleg, ttip = conic(d["assessment_type_distribution"])
    employee = model.get("external_context", {}).get("employee_count")
    employee_count_label = format_employee_count(employee)
    employee_text = f" from a global employee population of approximately <b>{employee_count_label}</b>" if employee_count_label else ""
    interpretation_note = data_interpretation_note(model, employee_text)

    css = f"""
.region-pie{{background:{rgrad} !important;}}
.type-pie{{background:{tgrad} !important;}}
.demo-panel .region-legend{{grid-template-columns:{'repeat(2, max-content)' if len(d['region_distribution']) > 2 else 'max-content'} !important;}}
"""
    jump_links = [
        ("about-data", "Data"),
        ("executive-narrative", "Executive"),
        ("interpretive-storyline", "Storyline"),
        ("benchmark-comparison", "Benchmark"),
        ("leadership-signals", "Signals"),
        ("functional-patterns", "Functions"),
        ("population-patterns", "Levels"),
        ("regional-patterns", "Regions"),
        ("follow-up-opportunities", "Follow-up"),
    ]
    jump_nav = "".join(f'<a class="jump-nav-link" href="#{section_id}">{esc(label)}</a>' for section_id, label in jump_links)
    toggle = benchmark_toggle(benchmarks)

    variant_blocks = {key: [] for key in ["executive-narrative", "interpretive-storyline", "benchmark-comparison", "leadership-signals", "functional-patterns", "population-patterns", "regional-patterns"]}
    for benchmark in benchmarks:
        bid = benchmark["id"]
        view = model_for_benchmark(model, bid)
        n = narrative_for_view(model, view, bid)
        attrs = view_attrs(benchmark, default_id)
        variant_blocks["executive-narrative"].append(f'<div {attrs}>{executive_section(view, n, c)}</div>')
        variant_blocks["interpretive-storyline"].append(f'<div {attrs}>{storyline_section(n, benchmark)}</div>')
        variant_blocks["benchmark-comparison"].append(f'<div {attrs}>{benchmark_section(view, c, benchmark)}</div>')
        variant_blocks["leadership-signals"].append(f'<div {attrs}>{signals_section(view, n, c)}</div>')
        hs = heatmap_sections(view, n, c, bid)
        # Split heatmap string by section markers for separate anchors.
        parts = hs.split('\n')
        variant_blocks["functional-patterns"].append(f'<div {attrs}>{parts[0]}</div>')
        variant_blocks["population-patterns"].append(f'<div {attrs}>{parts[1]}</div>')
        variant_blocks["regional-patterns"].append(f'<div {attrs}>{parts[2]}</div>')

    body = f"""
<div class="page">
<nav id="report-top" class="report-jump-nav show-identity" aria-label="Report section navigation"><div class="jump-nav-inner"><div class="jump-nav-identity"><a class="jump-nav-logo-link" href="#report-top" aria-label="Back to top"><img class="jump-nav-logo" src="{esc(logo_src)}" alt="Korn Ferry"/></a><div class="jump-nav-title"><span class="jump-nav-product">AI-Ready Leader Insights</span><span class="jump-nav-client">{esc(legal)}</span></div></div><div class="jump-nav-links">{jump_nav}</div>{toggle}</div></nav>
<header class="hero"><h1>{default_n['hero_h1']}</h1><p>{default_n['hero_p']}</p></header>
<section class="airl-explainer-section" aria-labelledby="airl-explainer-title"><div class="airl-explainer-header"><h2 id="airl-explainer-title">What is the AI-Ready Leader?</h2><a class="airl-explainer-button" href="https://www.kornferry.com/institute/introducing-the-ai-ready-leader" target="_blank" rel="noopener noreferrer">Learn More</a></div><p>AI-Ready Leaders help organizations turn AI ambition into practical impact. Korn Ferry’s AI-Ready Leader Success Profile focuses on the human leadership capabilities needed to set direction, mobilize teams, scale new ways of working, and build trust as AI changes how work gets done. It reflects Korn Ferry’s view that successful AI adoption depends not only on technology, but on leaders who can align people, decisions, and execution around new possibilities.</p></section>
<section id="about-data" class="about-data-section"><div class="section-kicker">About the data</div><h2>Assessment population and coverage</h2><div class="demo-panel"><div class="demo-chart demo-dates"><h3>Coverage</h3><div class="demo-date-metric participant-total"><b class="total-count">{d['total_participants']:,}</b><span>participants</span></div><div class="demo-date-metric"><b>{d['earliest_assessment']}</b><span>earliest assessment</span></div><div class="demo-date-metric"><b>{d['latest_assessment']}</b><span>latest assessment</span></div></div><div class="demo-chart demo-year"><h3>Assessment volume by year</h3><div class="year-bars">{bars(d['year_counts'])}</div></div><div class="demo-chart demo-level"><h3>Level distribution</h3><div class="level-bars">{bars(d['level_distribution'])}</div></div><div class="demo-chart"><h3>Regional mix</h3><div class="pie-row"><div class="pie region-pie" data-tooltip="{esc(rtip)}"></div><div class="pie-legend region-legend">{rleg}</div></div></div><div class="demo-chart"><h3>Assessment type</h3><div class="pie-row"><div class="pie type-pie" data-tooltip="{esc(ttip)}"></div><div class="pie-legend type-legend">{tleg}</div></div></div></div>{interpretation_note}</section>
{benchmark_variant_stack('executive-narrative', variant_blocks['executive-narrative'])}
{benchmark_variant_stack('interpretive-storyline', variant_blocks['interpretive-storyline'])}
{benchmark_variant_stack('benchmark-comparison', variant_blocks['benchmark-comparison'])}
{benchmark_variant_stack('leadership-signals', variant_blocks['leadership-signals'])}
{benchmark_variant_stack('functional-patterns', variant_blocks['functional-patterns'])}
{benchmark_variant_stack('population-patterns', variant_blocks['population-patterns'])}
{benchmark_variant_stack('regional-patterns', variant_blocks['regional-patterns'])}
{actions_section(default_view, default_n)}
{external_sources_section(model)}
</div>
"""
    footer = f"""<footer class="kf-page-footer"><strong>© 2026 Korn Ferry</strong> · AI-Ready Leader Insights · {esc(c)} preview<span class="ai-disclaimer">This has been produced with help from AI.  Check for accuracy.  Korn Ferry is responsible for all deliverables to clients regardless of production method.</span></footer>"""
    return css, body, footer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content_model")
    ap.add_argument("--template", default=str(Path(__file__).resolve().parents[1] / "assets" / "report_template.html"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-default-narrative", action="store_true", help="Development only: render without final narrative validation.")
    args = ap.parse_args()
    model = json.loads(Path(args.content_model).read_text(encoding="utf-8"))
    if not args.allow_default_narrative:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from validate_content_model import validate_model
        issues = validate_model(model, strict=True)
        if issues:
            print("ERROR: content model failed final narrative validation; render blocked.", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            print("Use --allow-default-narrative only for development/test renders.", file=sys.stderr)
            return 1
    tpl = Path(args.template).read_text(encoding="utf-8")
    css, body, footer = render(model)
    title = f"{model['client']['legal_name']} | AI-Ready Leader Pulse"
    html_out = tpl.replace("{{REPORT_TITLE}}", esc(title)).replace("{{DYNAMIC_CSS}}", css).replace("{{REPORT_BODY}}", body).replace("{{REPORT_FOOTER}}", footer)
    Path(args.out).write_text(html_out, encoding="utf-8")
    print(args.out)

if __name__ == "__main__":
    sys.exit(main())

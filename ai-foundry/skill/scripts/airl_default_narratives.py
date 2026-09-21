#!/usr/bin/env python3
"""Development-only fallback narrative scaffolding for AIRL report rendering.

This module exists to keep placeholder narrative and fallback action-card
scaffolding out of the main renderer. Final client-ready reports must provide
LLM-authored narrative with narrative_status=final; these helpers are only used
for development layout/smoke rendering or to visibly fill incomplete action rows.
"""

from airl_render_helpers import esc
from airl_view_model import pick_high_low

def default_narratives(model):
    """Create placeholder narratives from the content model.

    These are intentionally only fallback scaffolds. Final report generation should
    overwrite these fields with source-informed, client-specific consulting narrative
    using references/narrative_rules.md and source_context.md. Keep fallback text
    interpretive rather than label-led so accidental use does not produce a report
    that merely lists composite or construct names.
    """
    c = model["client"]["short_name"]
    m = model["metrics"]
    largest = m["largest_advantage"]; watch = m["watch_area"]
    largest_label = m.get("largest_advantage_label") or ("Largest Advantage" if float(largest.get("gap_vs_benchmark", 0)) > 0 else "Relative Strength")
    watch_context = m.get("watch_area_context") or ("lowest_positive" if float(watch.get("gap_vs_benchmark", 0)) > 0 else ("at_benchmark" if float(watch.get("gap_vs_benchmark", 0)) == 0 else "below_benchmark"))
    ai_context = model.get("external_context", {}).get("ai_strategy_summary") or "the client's AI and digital transformation agenda"
    function_low, function_high = pick_high_low(model["heatmaps"].get("function", []))
    level_low, level_high = pick_high_low(model["heatmaps"].get("level", []))
    region_low, region_high = pick_high_low(model["heatmaps"].get("region", []))
    def row_name(row): return row["cut_name"] if row else "the lower-readiness group"
    def strength_behavior(resp):
        behaviors = {
            "Sustain the Vision": "hold direction while the AI path continues to evolve",
            "Take Decisive Action": "make pragmatic calls before perfect information is available",
            "Scale for Impact": "prioritize the AI bets most likely to create enterprise value",
            "Don't Stop at Success": "keep iterating after early wins rather than allowing pilots to become static",
            "Champion Learning and Unlearning": "help teams shed outdated habits while building new AI-enabled capability",
            "Address Fears": "create trust and confidence as AI changes roles, work, and identity",
        }
        return behaviors.get(resp.get("responsibility") or resp.get("display"), "turn readiness into practical AI leadership behavior")
    def watch_behavior(resp):
        behaviors = {
            "Sustain the Vision": "AI work may lose connection to a clear enterprise story when results lag or priorities shift",
            "Take Decisive Action": "AI use cases may stay in discussion longer than the market or workforce can afford",
            "Scale for Impact": "experiments may remain fragmented instead of becoming repeatable sources of value",
            "Don't Stop at Success": "early wins may create complacency before the organization has learned how to keep improving",
            "Champion Learning and Unlearning": "teams may learn tools without changing the habits, workflows, and assumptions that limit value",
            "Address Fears": "unaddressed anxiety may slow adoption even when technical investment is strong",
        }
        return behaviors.get(resp.get("responsibility") or resp.get("display"), "readiness may not translate consistently into scaled AI adoption")
    defaults = {
        "hero_h1": f"{c}'s AI-readiness signal points to where leadership energy can turn ambition into adoption.",
        "hero_p": f"Leaders can create clarity, sustain trust, and move Human + AI work from experimentation toward practical value when the strongest signals are translated into consistent operating routines.",
        "executive_h2": "A leadership readiness pattern that should guide where AI transformation is accelerated, enabled, and protected from stall points.",
        "executive_p1": f"{c}'s results point to a leadership population with meaningful readiness to turn AI ambition into practical movement, while still showing where readiness will need to become more repeatable. The value of the pattern is not the score alone; it is the signal it gives about where leaders may already be able to mobilize AI-enabled change and where enablement should be more deliberate.",
        "executive_p2": f"This matters because {c} is operating in a context where AI value depends on leadership capacity, not technology alone. Against {ai_context}, the practical question is how to use stronger readiness pockets to create momentum while supporting populations where the leadership behaviors needed for trust, iteration, and scale may be less consistent.",
        "commercial_implication": f"Use the assessment as a deployment and development map: accelerate groups that appear ready to lead priority AI use cases, and design focused support where lower gaps could slow adoption, trust, or scale.",
        "largest_narrative": (
            f"This is a relative strength because it is the most favorable responsibility pattern in the data, even though it is still not above benchmark. For {c}, it should be treated as the strongest available starting point rather than proof of broad advantage; use it to identify behaviors that can be reinforced while the broader leadership system is strengthened."
            if float(largest.get("gap_vs_benchmark", 0)) <= 0 else
            f"This strength suggests leaders may be comparatively better positioned to {strength_behavior(largest)}. For {c}, that can become a strategic asset when it is pointed at priority AI use cases, made visible through operating routines, and connected to enterprise value rather than isolated local experimentation."
        ),
        "watch_narrative": (
            f"This is the lowest relative responsibility pattern, but it is still above benchmark. Read it as the place where {c} has the least room to coast, not as a deficit; sustaining this positive result may require clearer routines, expectations, and reinforcement as AI-enabled work scales."
            if float(watch.get("gap_vs_benchmark", 0)) > 0 else
            f"The watch area should be read as a potential scaling constraint, not a failure label. It signals that {watch_behavior(watch)}. Strengthening this area can help {c} convert early readiness into more repeatable adoption across teams, functions, and markets."
        ),
        "story_h2": "What the pattern means for AI-ready leadership.",
        "story_card_1_title": "The core question is where readiness can become enterprise momentum.",
        "story_card_1_text": f"The benchmark pattern should help {c} decide which leader populations can carry faster AI activation and which need more support before they are asked to model new ways of working.",
        "story_card_2_title": "The watch area is the constraint to design around.",
        "story_card_2_text": f"The practical risk is not that leaders lack all readiness; it is that weaker behaviors in the watch area could slow the move from pilot activity to repeatable value unless they are built into routines, coaching, and accountability.",
        "story_toggle_1_title": "Use the strongest responsibility as an adoption lever.",
        "story_toggle_1_text": f"Where leaders are better able to {strength_behavior(largest)}, they can be placed closer to priority AI use cases and used to generate proof points that other populations can learn from.",
        "story_toggle_2_title": "Treat the watch area as a design input for enablement.",
        "story_toggle_2_text": f"The lower relative pattern suggests where {c} may need clearer expectations, manager support, and reinforcement mechanisms so AI adoption does not depend only on local enthusiasm.",
        "story_toggle_3_title": "Behavioral signals explain why the pattern matters.",
        "story_toggle_3_text": f"The most differentiated signals point to behaviors that can create confidence and motion in ambiguity; the less differentiated signals point to where trust, judgment, learning, or scaling discipline may need more deliberate development.",
        "story_toggle_4_title": "Population patterns should shape how the work is sequenced.",
        "story_toggle_4_text": f"Function, level, and region results should guide where {c} pilots, enables, and scales first rather than relying on a single enterprise-wide activation model.",
        "signals_high_text": f"The highest differentiators point to behavioral conditions that can help leaders create clarity, confidence, and forward motion in AI-enabled change. Use the table as the evidence base, then focus the discussion on where leaders may already be able to mobilize teams through ambiguity and turn intent into action.",
        "signals_low_text": f"The relative watchpoints suggest where AI adoption may require more deliberate support. Use the table as the evidence base, then focus the discussion on potential constraints to trust, prioritization, experimentation, accountability, or sustained learning depending on the client context and population pattern.",
        "function_meaning_1_title": f"Support {row_name(function_low)} before asking it to carry change.",
        "function_meaning_1_text": f"This group shows the lowest average functional gap, so enablement should focus on the leadership behaviors needed to translate AI expectations into practical team routines.",
        "function_meaning_2_title": f"Use {row_name(function_high)} to generate proof points.",
        "function_meaning_2_text": f"This group appears better positioned to test AI-enabled ways of working, create examples of adoption, and share practices that other functions can adapt.",
        "function_meaning_3_title": "Sequence activation by readiness, not uniform rollout.",
        "function_meaning_3_text": "The function pattern should guide where to accelerate first and where to build confidence before increasing AI transformation expectations.",
        "level_meaning_1_title": f"Give {row_name(level_low)} clearer operating support.",
        "level_meaning_1_text": f"This leadership layer may need more concrete translation of AI ambition into role expectations, workflow changes, and manager routines.",
        "level_meaning_2_title": f"Use {row_name(level_high)} to model the change.",
        "level_meaning_2_text": f"This population can help make AI-ready leadership visible by translating enterprise ambition into practical expectations and adoption behaviors.",
        "level_meaning_3_title": "Tailor enablement by leadership layer.",
        "level_meaning_3_text": "Executives, managers, and individual contributors need different expectations for leading AI-enabled work, so activation should not use one generic message.",
        "region_meaning_1_title": f"Enable {row_name(region_low)} with context and confidence.",
        "region_meaning_1_text": f"This regional pattern suggests a need for clearer local support before broader AI leadership expectations are scaled.",
        "region_meaning_2_title": f"Learn from {row_name(region_high)}.",
        "region_meaning_2_text": f"This region may provide useful examples of how leaders create momentum, trust, or practical adoption in their local context.",
        "region_meaning_3_title": "Use regional results directionally.",
        "region_meaning_3_text": "Regional differences should shape inquiry and enablement, while participant counts and sample mix should temper overinterpretation.",
    }
    return {
        key: (f"[DEV PLACEHOLDER - rewrite before client use] {value}" if isinstance(value, str) else value)
        for key, value in defaults.items()
    }


def action_cards(model, n):
    c = model["client"]["short_name"]
    m = model["metrics"]
    f_low, f_high = pick_high_low(model["heatmaps"].get("function", []))
    f_low_name = f_low["cut_name"] if f_low else "lower-readiness functions"
    f_high_name = f_high["cut_name"] if f_high else "higher-readiness functions"
    defaults = [
        ("DEV PLACEHOLDER - replace recommendation", f"DEV PLACEHOLDER - replace before client use. Place stronger-readiness populations such as {f_high_name} close to priority AI work so {c} can turn assessment signals into visible examples of adoption, learning, and value creation."),
        ("DEV PLACEHOLDER - replace recommendation", "DEV PLACEHOLDER - replace before client use. Turn the watch area into specific expectations for how leaders make decisions, communicate, learn, and sustain progress after early AI activity begins."),
        ("DEV PLACEHOLDER - replace recommendation", f"DEV PLACEHOLDER - replace before client use. Focus enablement on {f_low_name} and other lower-gap groups so they have the context, tools, and leadership behaviors needed before broad scaling expectations increase."),
        ("DEV PLACEHOLDER - replace recommendation", "DEV PLACEHOLDER - replace before client use. Treat the strongest signal as a lever for practical deployment: identify leaders who can model the behavior, connect it to business outcomes, and transfer the practice across levels, functions, or regions."),
    ]
    cards = list(model.get("narrative", {}).get("follow_up_opportunities") or [])
    # Final reports should show four follow-up opportunities. If narrative
    # generation supplies fewer than four, fill the remaining slots with
    # deterministic scaffolds rather than silently rendering an incomplete row.
    if len(cards) < 4:
        cards.extend(defaults[len(cards):])
    parts = []
    for i, item in enumerate(cards[:4], 1):
        if isinstance(item, dict):
            title, text = item.get("title", "Follow-up opportunity"), item.get("text", "")
        else:
            title, text = item
        parts.append(f'<div class="action"><b>{i:02d}</b><h3 class="action-title">{esc(title)}</h3><p>{esc(text)}</p></div>')
    return "".join(parts)


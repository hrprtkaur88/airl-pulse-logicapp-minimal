"""
AI Foundry batch orchestrator.

For each client discovered in Blob 'data' for --run-month, runs the real
airl-pulse-report skill pipeline end to end:

  1. Download the client's AIRL assessment workbook (.xlsx).
  2. Validate it: ai-foundry/skill/scripts/validate_workbook.py.
  3. Build the deterministic content model: .../build_content_model.py.
  4. Ask Azure OpenAI (gpt-4o, via Managed Identity) to draft the narrative
     fields, grounded in SKILL.md + references/narrative_rules.md +
     references/output_contract.md + references/construct_composite_definitions.md,
     returning exactly the JSON shape validate_content_model.py enforces.
  5. Lint (.../lint_narrative_labels.py) and validate
     (.../validate_content_model.py) the merged content model. If either
     reports issues, feed them back to the LLM for up to
     NARRATIVE_REPAIR_PASSES additional attempts before giving up on this
     attempt (the existing per-client retry/backoff loop below still applies
     across attempts, so a client gets further tries on the next backoff).
  6. Render the final client-ready HTML: .../render_report.py (no
     --allow-default-narrative -- only fully validated, lint-clean narrative
     is ever rendered to a client-facing report).
  7. Upload dated + latest HTML to Blob 'report', write a status manifest.

Skill scripts under ai-foundry/skill/ are invoked as subprocesses, never
imported/monkeypatched. Per ai-foundry/README.md ("Do not fork or edit files
inside skill/"), each script's CLI is the intended integration boundary and
keeps this repo's copy of the skill package byte-identical to the upstream
Korn Ferry release.

ManagedIdentity via DefaultAzureCredential is used for Blob and Azure OpenAI.

Usage:
    python run_batch.py --run-month 092026
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import traceback
from copy import deepcopy

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
import openai

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[2]
SKILL_ROOT = REPO / "ai-foundry" / "skill"
SKILL_SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(REPO / "shared"))

from naming import (
    data_workbook_path, report_dated_path, report_latest_path,
    status_manifest_path, slugify,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ai-foundry.batch")

# Number of additional narrative drafting passes allowed within a single
# per-client attempt when lint/validation returns issues. The LLM is given
# the prior issues and asked to repair only the flagged fields. This is
# separate from the outer per-client retry/backoff loop, which covers
# transient failures (network, blob, OpenAI throttling).
NARRATIVE_REPAIR_PASSES = 4

REQUIRED_REFERENCE_FILES = [
    "SKILL.md",
    "references/narrative_rules.md",
    "references/output_contract.md",
    "references/construct_composite_definitions.md",
]

BASE_NARRATIVE_FIELDS = [
    "hero_h1", "hero_p",
    "executive_h2", "executive_p1", "executive_p2", "commercial_implication",
    "largest_narrative", "watch_narrative",
    "story_h2", "story_card_1_title", "story_card_1_text", "story_card_2_title", "story_card_2_text",
    "story_toggle_1_title", "story_toggle_1_text", "story_toggle_2_title", "story_toggle_2_text",
    "story_toggle_3_title", "story_toggle_3_text", "story_toggle_4_title", "story_toggle_4_text",
    "signals_high_text", "signals_low_text",
    "function_meaning_1_title", "function_meaning_1_text",
    "function_meaning_2_title", "function_meaning_2_text",
    "function_meaning_3_title", "function_meaning_3_text",
    "level_meaning_1_title", "level_meaning_1_text",
    "level_meaning_2_title", "level_meaning_2_text",
    "level_meaning_3_title", "level_meaning_3_text",
    "region_meaning_1_title", "region_meaning_1_text",
    "region_meaning_2_title", "region_meaning_2_text",
    "region_meaning_3_title", "region_meaning_3_text",
]


def ddmmyyyy(now: dt.datetime) -> str:
    return f"{now.day:02d}{now.month:02d}{now.year}"


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Run a skill script's CLI entrypoint as a subprocess.

    All ai-foundry/skill/scripts/*.py files are designed as standalone CLI
    tools (each has a __main__ entrypoint); invoking them this way keeps the
    skill package's own files completely untouched.

    The Azure Functions Python worker resolves third-party packages (pandas,
    openpyxl, ...) onto sys.path via its own worker bootstrap, which is not
    fully reflected in the process's inherited environment variables. A
    plain subprocess.run(..., env=None) child (default env inheritance)
    therefore cannot import them even though this parent process can. Force
    PYTHONPATH to mirror the parent's *resolved* sys.path so the child
    interpreter sees the exact same package locations.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    return subprocess.run(
        [sys.executable, *args], cwd=str(SKILL_SCRIPTS),
        capture_output=True, text=True, env=env,
    )


def load_reference_text() -> str:
    parts = []
    for rel in REQUIRED_REFERENCE_FILES:
        path = SKILL_ROOT / rel
        if not path.exists():
            raise RuntimeError(f"missing required skill reference file: {path}")
        parts.append(f"--- {rel} ---\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def list_clients_from_data(container, run_month: str) -> list[str]:
    suffix = f"/assessment-workbook-{run_month}.xlsx"
    clients = []
    for blob in container.list_blobs():
        if blob.name.endswith(suffix):
            clients.append(blob.name.split("/")[0])
    return sorted(set(clients))


def build_narrative_prompt(model: dict, prior_issues: list[str] | None, previous_draft: dict | None = None) -> str:
    benchmarks = model.get("benchmarks") or []
    benchmark_ids = [b["id"] for b in benchmarks] or ["overall"]

    per_benchmark_shape = ", ".join(f'"{f}": "..."' for f in BASE_NARRATIVE_FIELDS)
    benchmark_narratives_shape = ",\n".join(
        f'    "{bid}": {{ {per_benchmark_shape} }}' for bid in benchmark_ids
    )

    instructions = f"""
You are drafting the narrative for one AI-Ready Leader Pulse client report.
Follow SKILL.md, references/narrative_rules.md, references/output_contract.md,
and references/construct_composite_definitions.md exactly (all provided below
as system context). Write client-ready, insight-led prose -- not a data recap,
not label-led, no placeholder text, no reference to report generation process.

    Critical style rule: never write a sentence that strings together three or
    more construct/label names separated by commas (e.g. "...driven by Trust,
    Curiosity, and Adaptability" is NOT allowed). Instead, weave at most one or
    two construct names per sentence into natural prose, or describe the pattern
    without naming every construct (e.g. "the pattern spans several core
    capabilities, most notably trust and curiosity"). This applies to every
    field, including follow-up opportunities and all benchmark narrative sets.

    Critical executive-anchor rule (applies to executive_p1 + executive_p2 in
    EVERY benchmark narrative set you write, not just one): these two fields,
    combined, must contain EXACTLY ONE quantitative-or-benchmark-direction
    anchor -- not zero, not two or more. The reliable way to satisfy this
    precisely is to use exactly one short benchmark-direction phrase such as
    "above benchmark", "below benchmark", or "in line with benchmark" (no
    digits needed) rather than a numeric score or percentage. Do not use a raw
    participant count (e.g. "42 participants") as this anchor -- that belongs
    in About the Data, not the executive narrative. Do not include a second
    number/percentage/points figure anywhere else in executive_p1 or
    executive_p2.

    The full deterministic content model (client data, scores, benchmarks,
heatmaps, metrics) is provided as JSON below. Do not invent client data --
only interpret what is in the content model.

Return ONLY a single JSON object with exactly this shape (no markdown fences,
no commentary):

{{
  "follow_up_opportunities": [
    {{"title": "...", "text": "..."}},
    {{"title": "...", "text": "..."}},
    {{"title": "...", "text": "..."}},
    {{"title": "...", "text": "..."}}
  ],
  "benchmark_narratives": {{
{benchmark_narratives_shape}
  }}
}}

Rules:
- "follow_up_opportunities" must contain exactly four items; it is shared
  across benchmark views per output_contract.md.
- "benchmark_narratives" must contain one complete, standalone narrative set
  per benchmark id listed above ({', '.join(benchmark_ids)}). Each must
  independently satisfy narrative_rules.md section 4.1 (dual-benchmark
  narrative independence) -- do not compare the two benchmark views inside
  either narrative set, and do not name the alternate benchmark.
- Every field must be at least a few complete sentences (except *_title
  fields, which are short headlines/labels).
- Do not use placeholder, draft, or TODO language anywhere.
"""

    content_model_json = json.dumps(model, indent=2)
    prompt = instructions + "\n\nCONTENT MODEL:\n" + content_model_json

    if prior_issues:
        issues_text = "\n".join(f"- {issue}" for issue in prior_issues)
        previous_draft_json = json.dumps(previous_draft, indent=2) if previous_draft else "(not available)"
        prompt += (
            "\n\nThis is a TARGETED REPAIR pass, not a fresh draft. Here is the "
            "exact JSON object you returned previously:\n\n"
            f"PREVIOUS DRAFT:\n{previous_draft_json}\n\n"
            "That previous draft failed validation/lint with these specific "
            f"issues:\n{issues_text}\n\n"
            "Return a complete corrected JSON object with the exact same shape. "
            "Copy every field from the previous draft VERBATIM, character for "
            "character, EXCEPT the specific field(s) named in the issues above "
            "-- rewrite only those to fix the named issue while still fully "
            "satisfying every other rule in this prompt and the reference "
            "material. Do not rewrite, rephrase, or otherwise touch any field "
            "that was not named in an issue: fields not mentioned above already "
            "passed lint/validation and must be preserved exactly as-is."
        )
    return prompt


def call_llm_narrative(oai_client: "openai.AzureOpenAI", deployment: str, reference_text: str,
                        model: dict, prior_issues: list[str] | None,
                        previous_draft: dict | None = None) -> dict:
    system_prompt = (
        "You are a Korn Ferry consultant writing AI-Ready Leader Pulse client "
        "report narrative. Follow the skill reference material exactly.\n\n"
        + reference_text
    )
    user_prompt = build_narrative_prompt(model, prior_issues, previous_draft)

    # Repair passes are a targeted, low-creativity edit task (preserve
    # verbatim except the named fields) -- a lower temperature makes the
    # model far more likely to actually copy unaffected fields through
    # unchanged instead of subtly rephrasing them and reintroducing a
    # different lint violation elsewhere (the oscillation we saw in
    # testing). The first draft keeps a higher temperature for natural,
    # varied prose.
    temperature = 0.4 if prior_issues is None else 0.15

    resp = oai_client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=8000,
    )
    content = resp.choices[0].message.content
    return json.loads(content)


def merge_narrative(model: dict, llm_json: dict) -> dict:
    merged = deepcopy(model)
    benchmark_narratives = llm_json.get("benchmark_narratives", {})
    # Top-level "narrative" is the shared/default base that
    # ai-foundry/skill/scripts/airl_benchmarks.narrative_for_benchmark() overlays
    # with the per-benchmark dict (shared.update(benchmark_specific)). It is
    # also what validate_content_model.py's global positive-content checks
    # (hero/executive AI-term and benchmark-anchor checks) read directly, so it
    # must carry the default benchmark's full narrative -- not just
    # follow_up_opportunities -- or those checks fail against an empty dict
    # even when every benchmark_narratives.<bid> entry is complete.
    default_id = model.get("active_benchmark_id") or next(
        (b["id"] for b in (model.get("benchmarks") or []) if b.get("is_default")),
        (model.get("benchmarks") or [{"id": "overall"}])[0]["id"],
    )
    default_narrative = dict(benchmark_narratives.get(default_id, {}))
    default_narrative["follow_up_opportunities"] = llm_json.get("follow_up_opportunities", [])
    merged["narrative"] = default_narrative
    merged["benchmark_narratives"] = benchmark_narratives
    merged["narrative_status"] = "final"
    return merged


def lint_and_validate(model: dict) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as tmp:
        json.dump(model, tmp)
        tmp_path = pathlib.Path(tmp.name)
    try:
        issues: list[str] = []
        lint_proc = run_cli(["lint_narrative_labels.py", str(tmp_path), "--json"])
        if lint_proc.returncode not in (0, 1):
            raise RuntimeError(f"lint_narrative_labels.py errored: {lint_proc.stderr}")
        lint_result = json.loads(lint_proc.stdout or "{}")
        for issue in lint_result.get("issues", []):
            issues.append(f"[lint:{issue.get('code')}] {issue.get('path')}: {'; '.join(issue.get('reasons', []))}")

        validate_proc = run_cli(["validate_content_model.py", str(tmp_path), "--json"])
        if validate_proc.returncode not in (0, 1):
            raise RuntimeError(f"validate_content_model.py errored: {validate_proc.stderr}")
        validate_result = json.loads(validate_proc.stdout or "{}")
        for issue in validate_result.get("issues", []):
            issues.append(f"[validate:{issue.get('code')}] {issue.get('message', '')}")
        return issues
    finally:
        tmp_path.unlink(missing_ok=True)


def draft_and_validate_narrative(model: dict, oai_client, deployment: str, reference_text: str) -> tuple[dict, list[str]]:
    prior_issues: list[str] | None = None
    previous_draft: dict | None = None
    candidate = model
    last_issues: list[str] = []
    for attempt in range(NARRATIVE_REPAIR_PASSES + 1):
        llm_json = call_llm_narrative(oai_client, deployment, reference_text, model, prior_issues, previous_draft)
        candidate = merge_narrative(model, llm_json)
        last_issues = lint_and_validate(candidate)
        if not last_issues:
            return candidate, []
        log.warning("narrative draft attempt %d/%d had %d issue(s)", attempt + 1, NARRATIVE_REPAIR_PASSES + 1, len(last_issues))
        prior_issues = last_issues
        previous_draft = llm_json
    return candidate, last_issues


def process_client(slug: str, data_ct, report_ct, run_month: str, retries: int,
                    oai_client, deployment: str, reference_text: str) -> dict:
    now = dt.datetime.utcnow()
    workbook_blob_path = f"{slug}/assessment-workbook-{run_month}.xlsx"
    status = {
        "client_slug": slug,
        "run_month": run_month,
        "attempts": [],
        "status": "unknown",
        "latest_html_path": None,
        "dated_html_path": None,
    }

    for attempt in range(1, retries + 1):
        started = dt.datetime.utcnow().isoformat() + "Z"
        try:
            workbook_bytes = data_ct.get_blob_client(workbook_blob_path).download_blob().readall()

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = pathlib.Path(tmp_dir)
                workbook_path = tmp_dir_path / "workbook.xlsx"
                workbook_path.write_bytes(workbook_bytes)

                validate_proc = run_cli(["validate_workbook.py", str(workbook_path)])
                if validate_proc.returncode != 0:
                    raise RuntimeError(f"validate_workbook.py failed:\n{validate_proc.stdout}\n{validate_proc.stderr}")

                model_path = tmp_dir_path / "content_model.json"
                build_proc = run_cli(["build_content_model.py", str(workbook_path), "--out", str(model_path)])
                if build_proc.returncode != 0:
                    raise RuntimeError(f"build_content_model.py failed:\n{build_proc.stdout}\n{build_proc.stderr}")
                model = json.loads(model_path.read_text(encoding="utf-8"))

                final_model, issues = draft_and_validate_narrative(model, oai_client, deployment, reference_text)
                if issues:
                    raise RuntimeError(
                        f"narrative failed lint/validation after {NARRATIVE_REPAIR_PASSES + 1} attempt(s): "
                        + "; ".join(issues)
                    )

                final_model_path = tmp_dir_path / "content_model.final.json"
                final_model_path.write_text(json.dumps(final_model, indent=2), encoding="utf-8")

                html_path = tmp_dir_path / "report.html"
                render_proc = run_cli(["render_report.py", str(final_model_path), "--out", str(html_path)])
                if render_proc.returncode != 0:
                    raise RuntimeError(f"render_report.py failed:\n{render_proc.stdout}\n{render_proc.stderr}")
                html = html_path.read_text(encoding="utf-8")

            dated = report_dated_path(slug_to_name(slug), ddmmyyyy(now))
            latest = report_latest_path(slug_to_name(slug))
            html_bytes = html.encode("utf-8")
            report_ct.upload_blob(name=dated, data=html_bytes, overwrite=True)
            report_ct.upload_blob(name=latest, data=html_bytes, overwrite=True)
            status["attempts"].append({"n": attempt, "started": started, "outcome": "succeeded"})
            status["dated_html_path"] = dated
            status["latest_html_path"] = latest
            status["status"] = "succeeded"
            log.info("client %s succeeded on attempt %d", slug, attempt)
            return status
        except Exception as e:
            tb = traceback.format_exc()
            status["attempts"].append({
                "n": attempt, "started": started,
                "outcome": "failed", "error": str(e), "trace": tb,
            })
            log.warning("client %s attempt %d failed: %s", slug, attempt, e)
            if attempt < retries:
                time.sleep(2 ** attempt)

    status["status"] = "failed"
    return status


def slug_to_name(slug: str) -> str:
    # For file paths we only need the slug back; naming helper re-slugifies.
    # Passing slug through slugify() is a no-op for already-slugified input.
    return slug


def build_oai_client(endpoint: str, api_version: str) -> "openai.AzureOpenAI":
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return openai.AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-month", required=True, help="MMYYYY")
    parser.add_argument("--config", default=str(REPO / "config.json"))
    args = parser.parse_args()

    cfg = json.loads(pathlib.Path(args.config).read_text())
    storage_account = cfg["storageAccount"]
    data_name = cfg["containers"]["data"]
    report_name = cfg["containers"]["report"]
    retries = int(cfg["retries"]["aiFoundryPerClient"])
    oai_cfg = cfg["openai"]
    deployment = oai_cfg["chatDeployment"]
    oai_endpoint = f"https://{oai_cfg['account']}.openai.azure.com/"
    api_version = oai_cfg.get("apiVersion", "2024-10-21")

    account_url = f"https://{storage_account}.blob.core.windows.net/"
    cred = DefaultAzureCredential()
    bsc = BlobServiceClient(account_url=account_url, credential=cred)
    data_ct = bsc.get_container_client(data_name)
    report_ct = bsc.get_container_client(report_name)

    oai_client = build_oai_client(oai_endpoint, api_version)
    reference_text = load_reference_text()

    clients = list_clients_from_data(data_ct, args.run_month)
    log.info("discovered %d client workbooks for %s", len(clients), args.run_month)

    summary = {"run_month": args.run_month, "clients": []}
    for slug in clients:
        status = process_client(slug, data_ct, report_ct, args.run_month, retries,
                                 oai_client, deployment, reference_text)
        # Persist status manifest
        manifest_path = f"{slug}/status-{args.run_month}.json"
        report_ct.upload_blob(
            name=manifest_path,
            data=json.dumps(status, indent=2).encode("utf-8"),
            overwrite=True,
        )
        summary["clients"].append({
            "client_slug": slug, "status": status["status"],
            "attempts": len(status["attempts"]),
        })

    # Persist overall summary
    report_ct.upload_blob(
        name=f"_batch/summary-{args.run_month}.json",
        data=json.dumps(summary, indent=2).encode("utf-8"),
        overwrite=True,
    )
    log.info("Batch complete: %s", json.dumps(summary))
    failed = [c for c in summary["clients"] if c["status"] != "succeeded"]
    if failed:
        log.error("%d clients failed after retries", len(failed))
        sys.exit(2 if len(failed) < len(clients) else 3)


if __name__ == "__main__":
    main()

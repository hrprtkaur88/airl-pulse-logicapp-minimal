from __future__ import annotations

import datetime as dt
import json
import logging
import os
import pathlib
import sys

import azure.functions as func
import jwt
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from jwt import PyJWKClient

HERE = pathlib.Path(__file__).resolve()

if (HERE.parents[1] / "ai-foundry" / "jobs" / "run_batch.py").exists():
    REPO = HERE.parents[1]
else:
    REPO = HERE.parent

sys.path.insert(0, str(REPO / "ai-foundry" / "jobs"))
sys.path.insert(0, str(REPO / "shared"))

import run_batch  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("airl.report_function")

app = func.FunctionApp()

TENANT_ID = os.environ["TENANT_ID"]
ADMIN_CLIENT_ID = os.environ["ADMIN_CLIENT_ID"]
ALLOWED_ADMIN_OIDS = {
    oid.strip()
    for oid in os.environ.get("ADMIN_ALLOWED_PRINCIPAL_IDS", "").split(",")
    if oid.strip()
}
JWKS_CLIENT = PyJWKClient(f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys")


def validate_bearer(auth_header: str) -> tuple[bool, str]:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return False, "missing bearer token"

    token = auth_header.split(" ", 1)[1].strip()
    try:
        signing_key = JWKS_CLIENT.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=[f"api://{ADMIN_CLIENT_ID}", ADMIN_CLIENT_ID],
            issuer=[
                f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
                f"https://sts.windows.net/{TENANT_ID}/",
            ],
        )
    except Exception as exc:  # surfaced as 401; do not leak token details
        return False, f"invalid token: {type(exc).__name__}"

    oid = claims.get("oid") or claims.get("http://schemas.microsoft.com/identity/claims/objectidentifier")
    if not oid or oid not in ALLOWED_ADMIN_OIDS:
        return False, "principal not authorized for report generation"

    return True, ""


def json_response(payload: dict, status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


@app.function_name(name="GenerateReport")
@app.route(route="report-generation/generate-report/{slug}", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def generate_report(req: func.HttpRequest) -> func.HttpResponse:
    ok, error = validate_bearer(req.headers.get("Authorization", ""))
    if not ok:
        return func.HttpResponse(
            json.dumps({"error": error}),
            status_code=401,
            mimetype="application/json",
            headers={"WWW-Authenticate": f'Bearer authorization_uri="https://login.microsoftonline.com/{TENANT_ID}", resource="api://{ADMIN_CLIENT_ID}"'},
        )

    slug = req.route_params.get("slug")
    if not slug:
        return json_response({"error": "missing slug"}, 400)

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    run_month = body.get("runMonth") or req.params.get("runMonth") or dt.datetime.utcnow().strftime("%m%Y")
    storage_account = body.get("storageAccountName") or os.environ["STORAGE_ACCOUNT_NAME"]
    data_container = body.get("dataContainerName") or os.environ.get("DATA_CONTAINER_NAME", "data")
    report_container = body.get("reportContainerName") or os.environ.get("REPORT_CONTAINER_NAME", "report")
    openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    openai_deployment = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
    openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
    retries = int(os.environ.get("REPORT_GENERATION_RETRIES", "2"))

    try:
        credential = DefaultAzureCredential()
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net/",
            credential=credential,
        )
        data_client = blob_service.get_container_client(data_container)
        report_client = blob_service.get_container_client(report_container)

        openai_client = run_batch.build_oai_client(openai_endpoint, openai_api_version)
        reference_text = run_batch.load_reference_text()
        status = run_batch.process_client(
            slug,
            data_client,
            report_client,
            run_month,
            retries=retries,
            oai_client=openai_client,
            deployment=openai_deployment,
            reference_text=reference_text,
        )

        manifest_path = f"{slug}/status-{run_month}.json"
        report_client.upload_blob(
            name=manifest_path,
            data=json.dumps(status, indent=2).encode("utf-8"),
            overwrite=True,
        )
    except Exception:
        log.exception("report generation failed for slug=%s runMonth=%s", slug, run_month)
        return json_response(
            {"error": "internal error generating report", "slug": slug, "runMonth": run_month},
            500,
        )

    return json_response(status, 200 if status.get("status") == "succeeded" else 500)

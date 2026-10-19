import base64
import json
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI(title="SAP C4C Ticket Redirect")

# Production SAP C4C SSO tenant.
# This can still be overridden in Render with the SAP_BASE_URL environment variable.
SAP_BASE_URL = os.getenv(
    "SAP_BASE_URL",
    "https://my361573-sso.crm.ondemand.com",
)

# Existing-ticket SAP navigation component.
SAP_EXISTING_TICKET_TARGET = os.getenv(
    "SAP_EXISTING_TICKET_TARGET",
    "/BYD_COD/ServiceOnDemand/Collaboration/COD_SR_TI.TI.uicomponent",
)

# Existing-ticket winId captured from the working SAP navigation URL.
# Keeping it configurable makes it easy to change in Render without editing code.
SAP_EXISTING_TICKET_WIN_ID = os.getenv(
    "SAP_EXISTING_TICKET_WIN_ID",
    "0625093873c9d4006d4beebf4f94c519",
)

# New-ticket / Service Request Quick Create component from the production tenant.
SAP_NEW_TICKET_TARGET = os.getenv(
    "SAP_NEW_TICKET_TARGET",
    "/BYD_COD/ServiceOnDemand/AgentQueue/SEOD_ServiceRequest_QC.QC.uicomponent",
)

# winId captured from the production New Ticket URL.
SAP_NEW_TICKET_WIN_ID = os.getenv(
    "SAP_NEW_TICKET_WIN_ID",
    "ea7502c78ba52df9e11cc93a536e15c1",
)

OBJECT_ID_PATTERN = re.compile(r"^[A-Fa-f0-9]{32}$")


def build_sap_navigation_url(payload: dict) -> str:
    """Build the SAP C4C SSO navigation URL from a navigation payload."""
    payload_json = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    encoded_payload = base64.b64encode(
        payload_json.encode("utf-8")
    ).decode("ascii")

    return (
        f"{SAP_BASE_URL}/sap/ap/ui/repository/SAP_UI/HTML5/newclient.html"
        "?app.component=/SAP_UI_CT/Main/root.uiccwoc"
        "&rootWindow=X"
        "&redirectUrl=/sap/byd/runtime"
        f"#Nav/1/{encoded_payload}"
    )


@app.get("/")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "sap_base_url": SAP_BASE_URL,
    }


# IMPORTANT:
# Keep this route ABOVE /sap/ticket/{object_id} so FastAPI does not
# interpret the literal word "new" as an ObjectID.
@app.get("/sap/ticket/new")
def open_new_sap_ticket() -> RedirectResponse:
    navigation_payload = {
        "context": None,
        "target": SAP_NEW_TICKET_TARGET,
        "winId": SAP_NEW_TICKET_WIN_ID,
    }

    redirect_url = build_sap_navigation_url(navigation_payload)
    return RedirectResponse(url=redirect_url, status_code=302)


@app.get("/sap/ticket/{object_id}")
def open_sap_ticket(object_id: str) -> RedirectResponse:
    normalized_object_id = object_id.strip().replace("-", "")

    if not OBJECT_ID_PATTERN.fullmatch(normalized_object_id):
        raise HTTPException(
            status_code=400,
            detail="SAP ticket ObjectID must be 32 hexadecimal characters.",
        )

    navigation_payload = {
        "thingparams": {
            "Key": normalized_object_id.upper(),
            "SourcePath": "/Root/UUID",
        },
        "inPort": "Inspect",
        "target": SAP_EXISTING_TICKET_TARGET,
        "winId": SAP_EXISTING_TICKET_WIN_ID,
    }

    redirect_url = build_sap_navigation_url(navigation_payload)
    return RedirectResponse(url=redirect_url, status_code=302)

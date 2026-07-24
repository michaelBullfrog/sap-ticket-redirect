import base64
import json
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI(title="SAP C4C Ticket Redirect")

SAP_BASE_URL = os.getenv(
    "SAP_BASE_URL",
    "https://my359164-sso.crm.ondemand.com",
)

SAP_TARGET = (
    "/BYD_COD/ServiceOnDemand/Collaboration/"
    "COD_SR_TI.TI.uicomponent"
)

OBJECT_ID_PATTERN = re.compile(r"^[A-Fa-f0-9]{32}$")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


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
        "target": SAP_TARGET,
        "winId": "0625093873c9d4006d4beebf4f94c519",
    }

    payload_json = json.dumps(
        navigation_payload,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    encoded_payload = base64.b64encode(
        payload_json.encode("utf-8")
    ).decode("ascii")

    redirect_url = (
        f"{SAP_BASE_URL}/sap/ap/ui/repository/SAP_UI/HTML5/newclient.html"
        "?app.component=/SAP_UI_CT/Main/root.uiccwoc"
        "&rootWindow=X"
        "&redirectUrl=/sap/byd/runtime"
        f"#Nav/1/{encoded_payload}"
    )

    return RedirectResponse(url=redirect_url, status_code=302)

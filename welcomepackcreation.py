#!/usr/bin/env python3
"""
build_welcome_packets.py

Creates ONE merged PDF per customer account:
  1) Welcome letter PDF generated from welcomepacket-data/letter-template.html
     using Salesforce-style merge fields:
       - {{{Account.Name}}}              (we map to Account__r.Owner.Name_Formula__c by request)
       - {{{Account.BillingAddress}}}    (we build from BillingStreet/City/State/Postal)
  2) Append W9 PDF
  3) Append Customer Declaration Form PDF
Then zips all customer PDFs into one ZIP.

Requires:
  pip install simple-salesforce weasyprint pypdf

WeasyPrint system deps (Ubuntu):
  sudo apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader, PdfWriter
from simple_salesforce import Salesforce

# WeasyPrint import can fail if system deps aren't installed; handle gracefully.
try:
    from weasyprint import HTML
except Exception as e:  # noqa: BLE001
    HTML = None
    _WEASYPRINT_IMPORT_ERROR = e


# --------------------------------------------------------------------------------------
# Paths (relative to repo root)
# --------------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "welcomepacket-data"
W9_PDF = DATA_DIR / "W9 - Bluebird Midwest LLC dba Bluebird Fiber.pdf"
DECLARATION_PDF = DATA_DIR / "Bluebird Fiber Customer (BMW) Declaration Form.pdf"
LETTER_TEMPLATE_HTML = DATA_DIR / "letter-template.html"
SIGNATURE_PNG = DATA_DIR / "jason-signature.png"
COMBINED_LOGO_PNG = DATA_DIR / "combinedlogo.png"

OUTPUT_DIR = ROOT / "welcomepacket-out"


# --------------------------------------------------------------------------------------
# Salesforce configuration
# --------------------------------------------------------------------------------------

BILLING_INVOICE_OBJECT = "Billing_Invoice__c"
BILLING_INVOICE_FLAG_FIELD = "BBF_Ban__c"

# IMPORTANT: your query uses Account__r.*, which implies the lookup is Account__c
BILLING_INVOICE_ACCOUNT_LOOKUP = "Account__c"


# --------------------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class AccountRow:
    id: str
    # Name line requested by you:
    owner_name_formula: str

    billing_street: str
    billing_city: str
    billing_state: str
    billing_postal: str


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ensure_files_exist() -> None:
    missing = []
    for p in [
        W9_PDF,
        DECLARATION_PDF,
        LETTER_TEMPLATE_HTML,
        SIGNATURE_PNG,
        COMBINED_LOGO_PNG,
    ]:
        if not p.exists():
            missing.append(str(p))
    if missing:
        die("Missing required files:\n  " + "\n  ".join(missing))


def sanitize_filename(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9 _.-]+", "", (s or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:120] if s else "Account"


def format_billing_address(a: AccountRow) -> str:
    """
    Build the address block *exactly* from BillingStreet/City/State/Postal.
    (Do NOT inject the name line here; the template already prints the name.)
    """
    lines: List[str] = []

    street = (a.billing_street or "").strip()
    if street:
        for part in street.splitlines():
            part = part.strip()
            if part:
                lines.append(part)

    city = (a.billing_city or "").strip()
    state = (a.billing_state or "").strip()
    postal = (a.billing_postal or "").strip()

    city_state = ", ".join([x for x in [city, state] if x])
    if postal:
        city_state = f"{city_state} {postal}".strip()
    if city_state:
        lines.append(city_state)

    return "\n".join(lines)


def render_letter_html(template_html: str, name_line: str, billing_address: str) -> str:
    """
    Replace Salesforce Classic merge fields with real values.

    Your template uses:
      {{{Account.Name}}}
      {{{Account.BillingAddress}}}

    We map Account.Name -> Account__r.Owner.Name_Formula__c (per your requirement).
    """
    html = template_html

    # Triple-brace placeholders
    html = html.replace("{{{Account.Name}}}", name_line)
    html = html.replace("{{{Account.BillingAddress}}}", billing_address)

    # If template still has older classic placeholders, attempt to replace them too.
    html = html.replace("{!Account.OwnerFullName}", name_line)
    html = html.replace("{!Account.BillingAddress}", billing_address)

    return html


def html_to_pdf_bytes(html_str: str, base_url: Path) -> bytes:
    if HTML is None:
        die(
            "WeasyPrint failed to import. Install python package AND system dependencies.\n"
            f"Import error: {_WEASYPRINT_IMPORT_ERROR}"
        )

    # base_url ensures relative paths in HTML resolve correctly (e.g. combinedlogo.png)
    doc = HTML(string=html_str, base_url=str(base_url)).render()
    return doc.write_pdf()


def zip_outputs(zip_path: Path, files: List[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=p.name)


from io import BytesIO  # noqa: E402


# --------------------------------------------------------------------------------------
# Salesforce
# --------------------------------------------------------------------------------------


def sf_login_from_env() -> Salesforce:
    """
    HARD-CODED Salesforce login for demo/testing only.
    """

    ES_USERNAME = "sfdcapi@everstream.net"
    ES_PASSWORD = "pV4CAxns8DQtJsBq!"
    ES_TOKEN = "r1uoYiusK19RbrflARydi86TA"
    ES_DOMAIN = "login"  # use "test" for sandbox

    return Salesforce(
        username=ES_USERNAME,
        password=ES_PASSWORD,
        security_token=ES_TOKEN,
        domain=ES_DOMAIN,
    )


def fetch_accounts_with_bbf_bans(sf: Salesforce) -> List[AccountRow]:
    # Use the query YOU provided (plus Account__r.Id for dedupe, and Account__c for safety)
    soql = f"""
    SELECT
      {BILLING_INVOICE_ACCOUNT_LOOKUP},
      Account__r.Id,
      Account__r.Owner.Name_Formula__c,
      Account__r.BillingStreet,
      Account__r.BillingCity,
      Account__r.BillingState,
      Account__r.BillingPostalCode
    FROM {BILLING_INVOICE_OBJECT}
    WHERE {BILLING_INVOICE_FLAG_FIELD} = true
      AND {BILLING_INVOICE_ACCOUNT_LOOKUP} != null
      LIMIT 1
    """

    recs = sf.query_all(soql)["records"]

    # DEDUPE: one PDF per Account
    seen: Dict[str, AccountRow] = {}
    for r in recs:
        ar = r.get("Account__r") or {}
        aid = ar.get("Id") or r.get(BILLING_INVOICE_ACCOUNT_LOOKUP)
        if not aid:
            continue
        if aid in seen:
            continue  # already processed this Account

        owner_name_formula = (ar.get("Owner", {}) or {}).get("Name_Formula__c", "")
        # NOTE: Sometimes SF returns it as a flat key on Account__r depending on API version.
        # If the above comes back empty, try flat access:
        if not owner_name_formula:
            owner_name_formula = ar.get("Owner.Name_Formula__c", "") or ar.get(
                "OwnerName_Formula__c", ""
            )

        row = AccountRow(
            id=aid,
            owner_name_formula=(owner_name_formula or "").strip(),
            billing_street=(ar.get("BillingStreet") or ""),
            billing_city=(ar.get("BillingCity") or ""),
            billing_state=(ar.get("BillingState") or ""),
            billing_postal=(ar.get("BillingPostalCode") or ""),
        )
        seen[aid] = row

    return list(seen.values())


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------


def main() -> None:
    ensure_files_exist()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    template_html = LETTER_TEMPLATE_HTML.read_text(encoding="utf-8")

    sf = sf_login_from_env()
    accounts = fetch_accounts_with_bbf_bans(sf)

    if not accounts:
        print("No eligible accounts found (Billing_Invoice__c.BBF_Ban__c = true).")
        return

    out_files: List[Path] = []

    for a in accounts:
        billing_addr = format_billing_address(a)

        demo_name = "Vincent Lettau"
        demo_address = "300 S. Washington Square Suite 140\nLansing, MI 48933"
        rendered = render_letter_html(template_html, demo_name, demo_address)
        # Map template "Account.Name" to Owner.Name_Formula__c per your requirement
        # rendered = render_letter_html(template_html, a.owner_name_formula, billing_addr)

        # Render letter PDF
        pdf_bytes = html_to_pdf_bytes(rendered, base_url=DATA_DIR)

        # Merge packet: letter + W9 + Declaration
        # out_name = f"{sanitize_filename(a.owner_name_formula)}_{a.id}.pdf"
        out_name = f"{sanitize_filename(demo_name)}_{a.id}.pdf"

        out_path = OUTPUT_DIR / out_name

        writer = PdfWriter()

        first = PdfReader(BytesIO(pdf_bytes))
        for p in first.pages:
            writer.add_page(p)

        for pth in [W9_PDF, DECLARATION_PDF]:
            reader = PdfReader(str(pth))
            for p in reader.pages:
                writer.add_page(p)

        with out_path.open("wb") as f:
            writer.write(f)

        out_files.append(out_path)
        print(f"Built: {out_path}")

    zip_path = OUTPUT_DIR / f"welcome_packets_{date.today().isoformat()}.zip"
    zip_outputs(zip_path, out_files)
    print(f"\nZIP ready: {zip_path}")


if __name__ == "__main__":
    main()

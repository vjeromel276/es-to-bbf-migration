#!/usr/bin/env python3
"""
Two-Step Export for Line_Card__c and Rack__c
These objects require nested subqueries which SOQL doesn't support,
so we query in two steps using Python.

Requirements:
    pip install simple-salesforce

Usage:
    python sf_export_nested.py

Configuration:
    Set environment variables:
        SF_USERNAME=your.email@company.com
        SF_PASSWORD=yourpassword
        SF_SECURITY_TOKEN=yoursecuritytoken
        SF_DOMAIN=login  (or 'test' for sandbox)
"""

import os
import csv
from datetime import datetime
from pathlib import Path

try:
    from simple_salesforce import Salesforce
except ImportError:
    print("Required package not found. Install with:")
    print("  pip install simple-salesforce")
    exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    "username": "sfdcapi@everstream.net",
    "password": "pV4CAxns8DQtJsBq!",
    "security_token": "r1uoYiusK19RbrflARydi86TA",
    "domain": "login",
}

OUTPUT_DIR = Path("./sf_exports")

# Base WHERE clause for Order filtering
ORDER_BASE_WHERE = """Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
    AND (NOT Project_Group__c LIKE '%PA MARKET DECOM%')
    AND Service_Order_Record_Type__c = 'Service Order Agreement'
    AND Billing_Invoice__r.BBF_Ban__c = true"""

# Field lists
LINE_CARD_FIELDS = [
    "Id",
    "IsDeleted",
    "Name",
    "CreatedDate",
    "CreatedById",
    "LastModifiedDate",
    "LastModifiedById",
    "SystemModstamp",
    "LastActivityDate",
    "LastViewedDate",
    "LastReferencedDate",
    "Network_Element__c",
    "Line_Card_Type__c",
    "Line_Card_Description__c",
    "Line_Card_Detail__c",
    "Slot__c",
    "Comments__c",
    "Fixed_Asset_Inventory__c",
    "Unit_ID__c",
    "Serial_Number__c",
    "Line_Card_Class__c",
    "Open_Slot__c",
    "Reserved_By__c",
    "Reserved_Date__c",
    "Line_Card_Type_Lookup__c",
    "Comment_Box_Core__c",
    "Comment_Box__c",
    "Firmware_Version_Core__c",
    "Line_Card_Details_Core__c",
    "TrLineCardDetails__c",
    "Tr_LineCardType__c",
    "Part_Number_Core__c",
    "Part_Number_Transport__c",
    "Serial_Number_Core__c",
    "Serial_Number_Transport__c",
    "Slot_Core__c",
    "Slot_Transport__c",
    "Status_Transport__c",
    "Design_Layout__c",
    "TR_Optic_Component__c",
    "TR_Optic_Part__c",
    "TR_Optic_Serial_Number__c",
    "TR_Optic_Vendor__c",
    "TR_Optic_Wavelenght__c",
]

RACK_FIELDS = [
    "Name",
    "Id",
    "IsDeleted",
    "CreatedDate",
    "CreatedById",
    "LastModifiedDate",
    "LastModifiedById",
    "SystemModstamp",
    "LastActivityDate",
    "LastViewedDate",
    "LastReferencedDate",
    "Related_Facility__c",
    "Rack_Type__c",
    "Rack_Number__c",
    "Comments__c",
    "Rack_WIdth__c",
    "A_Power__c",
    "B_Power__c",
    "Volts_A__c",
    "Volts_B__c",
    "Amps_A__c",
    "Amps_B__c",
    "Site_ID__c",
    "Facility_Common_Name__c",
]


# =============================================================================
# FUNCTIONS
# =============================================================================


def connect_to_salesforce():
    """Establish connection to Salesforce."""
    print("Connecting to Salesforce...")

    if not CONFIG["username"] or not CONFIG["password"]:
        print("\nERROR: Salesforce credentials not configured.")
        print("Set environment variables:")
        print("  export SF_USERNAME='your.email@company.com'")
        print("  export SF_PASSWORD='yourpassword'")
        print("  export SF_SECURITY_TOKEN='yoursecuritytoken'")
        print("  export SF_DOMAIN='login'")
        exit(1)

    try:
        sf = Salesforce(
            username=CONFIG["username"],
            password=CONFIG["password"],
            security_token=CONFIG["security_token"],
            domain=CONFIG["domain"],
        )
        print(f"  Connected to: {sf.sf_instance}")
        return sf
    except Exception as e:
        print(f"  ERROR: Failed to connect - {e}")
        exit(1)


def flatten_record(record, parent_key=""):
    """Flatten nested dictionaries in a record."""
    items = {}
    for key, value in record.items():
        if key == "attributes":
            continue
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_record(value, new_key))
        else:
            items[new_key] = value
    return items


def query_ids(sf, query):
    """Execute query and return list of IDs."""
    print(f"  Executing ID query...")
    try:
        results = sf.query_all(query)
        ids = [r["Id"] for r in results.get("records", [])]
        print(f"  Found {len(ids)} IDs")
        return ids
    except Exception as e:
        print(f"  ERROR: {e}")
        return []


def query_with_ids(sf, object_name, fields, id_field, ids):
    """Query object filtering by a list of IDs."""
    if not ids:
        print(f"  No IDs to query - skipping {object_name}")
        return []

    all_records = []
    chunk_size = 200  # SOQL IN clause limit

    print(
        f"  Querying {object_name} in {(len(ids) + chunk_size - 1) // chunk_size} chunks..."
    )

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        ids_str = "'" + "','".join(chunk) + "'"

        field_list = ", ".join(fields)
        query = (
            f"SELECT {field_list} FROM {object_name} WHERE {id_field} IN ({ids_str})"
        )

        try:
            results = sf.query_all(query)
            records = results.get("records", [])
            all_records.extend([flatten_record(r) for r in records])
        except Exception as e:
            print(f"  ERROR on chunk {i//chunk_size + 1}: {e}")

    print(f"  Retrieved {len(all_records)} total records")
    return all_records


def save_to_csv(records, object_name, output_dir):
    """Save records to CSV file."""
    if not records:
        print(f"  No records to save for {object_name}")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"{object_name}_{timestamp}.csv"

    all_keys = set()
    for record in records:
        all_keys.update(record.keys())

    fieldnames = sorted(all_keys)
    if "Id" in fieldnames:
        fieldnames.remove("Id")
        fieldnames.insert(0, "Id")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"  Saved to: {filename}")
    return filename


# =============================================================================
# MAIN
# =============================================================================


def main():
    print("=" * 70)
    print("TWO-STEP EXPORT: Line_Card__c and Rack__c")
    print("=" * 70)
    print()

    sf = connect_to_salesforce()
    print()

    results = []

    # =========================================================================
    # LINE_CARD__c (via Network_Element__c -> Order)
    # =========================================================================
    print("-" * 70)
    print("[Line_Card__c] Two-step query")
    print("-" * 70)

    print("\nStep 1: Get Network_Element__c IDs from filtered Orders...")
    ne_query = f"""
        SELECT Id FROM Network_Element__c 
        WHERE Service_Order__c IN (
            SELECT Id FROM Order WHERE {ORDER_BASE_WHERE}
        )
    """
    ne_ids = query_ids(sf, ne_query)

    print("\nStep 2: Query Line_Card__c for those Network Elements...")
    line_cards = query_with_ids(
        sf, "Line_Card__c", LINE_CARD_FIELDS, "Network_Element__c", ne_ids
    )

    if line_cards:
        filepath = save_to_csv(line_cards, "Line_Card__c", OUTPUT_DIR)
        results.append(
            {"object": "Line_Card__c", "records": len(line_cards), "status": "SUCCESS"}
        )
    else:
        results.append({"object": "Line_Card__c", "records": 0, "status": "NO DATA"})

    print()

    # =========================================================================
    # RACK__c (via Facility__c -> Order)
    # =========================================================================
    print("-" * 70)
    print("[Rack__c] Two-step query")
    print("-" * 70)

    print("\nStep 1: Get Facility__c IDs from filtered Orders...")
    # Need to get facilities from all three Order lookup fields
    facility_ids = set()

    for field in ["Facility__c", "Facility_address_z_a__c", "Facility_Address_Z_b__c"]:
        fac_query = f"""
            SELECT {field} FROM Order 
            WHERE {ORDER_BASE_WHERE} AND {field} != null
        """
        try:
            results_query = sf.query_all(fac_query)
            for r in results_query.get("records", []):
                if r.get(field):
                    facility_ids.add(r[field])
        except Exception as e:
            print(f"  Warning: Error querying {field}: {e}")

    facility_ids = list(facility_ids)
    print(f"  Found {len(facility_ids)} unique Facility IDs")

    print("\nStep 2: Query Rack__c for those Facilities...")
    racks = query_with_ids(
        sf, "Rack__c", RACK_FIELDS, "Related_Facility__c", facility_ids
    )

    if racks:
        filepath = save_to_csv(racks, "Rack__c", OUTPUT_DIR)
        results.append(
            {"object": "Rack__c", "records": len(racks), "status": "SUCCESS"}
        )
    else:
        results.append({"object": "Rack__c", "records": 0, "status": "NO DATA"})

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)
    print(f"{'Object':<25} {'Records':>10}  {'Status':<15}")
    print("-" * 70)
    for r in results:
        print(f"{r['object']:<25} {r['records']:>10}  {r['status']:<15}")
    print("=" * 70)
    print(f"\nFiles saved to: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()

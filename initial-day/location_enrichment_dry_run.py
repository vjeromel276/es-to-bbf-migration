#!/usr/bin/env python3
"""
Location Enrichment DRY RUN
===========================
This script shows what Day 2 enrichment would do WITHOUT making any changes.

Day 1 fields already migrated:
- Name, City__c, State__c, County__c, PostalCode__c, Street__c
- Full_Address__c, CLLICode__c, businessUnit__c, OwnerId, ES_Legacy_ID__c

Day 2 enrichment adds:
- Loc__c (Geolocation) from Geocode_Lat_Long__c
- old_SiteId__c from Site_ID__c
- Common_Name__c from Organization__c
- Address_Validated_By__c from Verification_Used__c
- Address_API_Message__c from Address_Return_Code__c
- Market__c from Dimension_4_Market__c
- Legacy_CLLI_Code__c from CLLI__c
- StateCode__c from State__c
- strName__c from Thoroughfare_Name__c
- Unique_Key__c from Unique_Constraint_Check__c
"""

from simple_salesforce import Salesforce
from collections import Counter
import sys

# =============================================================================
# CONFIGURATION
# =============================================================================

# ES UAT Credentials
ES_USERNAME = "sfdcapi@everstream.net.uat"
ES_PASSWORD = "ZXasqw1234!@#$"
ES_TOKEN = "X0ation2CNmK5C0pV94M6vFYS"
ES_DOMAIN = "test"

# BBF Credentials
BBF_USERNAME = "vlettau@everstream.net"
BBF_PASSWORD = "MNlkpo0987)(*&"
BBF_TOKEN = "I4xmQLmm03cXl1O9qI2Z3XAAX"
BBF_DOMAIN = "test"

# Picklist value mappings
VERIFICATION_TO_VALIDATED_BY = {
    "SmartyStreets": "SmartyStreets",
    "Google Maps": "Google",
    "UPS": None,  # No direct mapping - needs business decision
}

# =============================================================================
# CONNECT TO SALESFORCE
# =============================================================================

print("=" * 80)
print("LOCATION ENRICHMENT - DRY RUN")
print("=" * 80)
print("\nThis script shows what enrichment would do WITHOUT making changes.\n")

print("Connecting to ES (source)...")
es_sf = Salesforce(
    username=ES_USERNAME,
    password=ES_PASSWORD,
    security_token=ES_TOKEN,
    domain=ES_DOMAIN,
)
print(f"  Connected: {es_sf.sf_instance}")

print("Connecting to BBF (target)...")
bbf_sf = Salesforce(
    username=BBF_USERNAME,
    password=BBF_PASSWORD,
    security_token=BBF_TOKEN,
    domain=BBF_DOMAIN,
)
print(f"  Connected: {bbf_sf.sf_instance}")

# =============================================================================
# QUERY DATA
# =============================================================================

print("\n" + "-" * 80)
print("QUERYING DATA")
print("-" * 80)

# Query ES Address__c records that have been migrated (have BBF_New_Id__c)
es_query = """
SELECT Id, BBF_New_Id__c, Name,
       Geocode_Lat_Long__c, Geocode_Lat_Long__Latitude__s, Geocode_Lat_Long__Longitude__s,
       Site_ID__c, Organization__c,
       Verification_Used__c, Address_Return_Code__c,
       Dimension_4_Market__c, CLLI__c, State__c,
       Thoroughfare_Name__c, Unique_Constraint_Check__c
FROM Address__c
WHERE BBF_New_Id__c != null
"""

print("\nQuerying ES Address__c (migrated records with enrichment fields)...")
es_result = es_sf.query_all(es_query)
es_records = es_result["records"]
print(f"  Found {len(es_records)} migrated Address__c records in ES")

# Build lookup by ES Id
es_lookup = {r["Id"]: r for r in es_records}

# Query BBF Location__c records
bbf_query = """
SELECT Id, ES_Legacy_ID__c, Name,
       Loc__c, Loc__Latitude__s, Loc__Longitude__s,
       old_SiteId__c, Common_Name__c,
       Address_Validated_By__c, Address_API_Message__c,
       Market__c, Legacy_CLLI_Code__c, StateCode__c,
       strName__c, Unique_Key__c
FROM Location__c
WHERE ES_Legacy_ID__c != null
"""

print("Querying BBF Location__c (records with ES_Legacy_ID__c)...")
bbf_result = bbf_sf.query_all(bbf_query)
bbf_records = bbf_result["records"]
print(f"  Found {len(bbf_records)} Location__c records in BBF with ES_Legacy_ID__c")

# =============================================================================
# ANALYZE ENRICHMENT OPPORTUNITIES
# =============================================================================

print("\n" + "-" * 80)
print("ANALYZING ENRICHMENT OPPORTUNITIES")
print("-" * 80)

# Field mapping: BBF field -> ES field
ENRICHMENT_FIELDS = {
    "Loc__c": (
        "Geocode_Lat_Long__Latitude__s",
        "Geocode_Lat_Long__Longitude__s",
    ),  # Special: geolocation
    "old_SiteId__c": "Site_ID__c",
    "Common_Name__c": "Organization__c",
    "Address_Validated_By__c": "Verification_Used__c",  # Needs picklist translation
    "Address_API_Message__c": "Address_Return_Code__c",
    "Market__c": "Dimension_4_Market__c",
    "Legacy_CLLI_Code__c": "CLLI__c",
    "StateCode__c": "State__c",
    "strName__c": "Thoroughfare_Name__c",
    "Unique_Key__c": "Unique_Constraint_Check__c",
}

# Track statistics
stats = {
    "total_bbf_records": len(bbf_records),
    "matched_to_es": 0,
    "fields_to_enrich": Counter(),
    "fields_already_populated": Counter(),
    "es_field_null": Counter(),
    "sample_updates": [],
}

# Picklist value distribution
verification_values = Counter()
dimension4_values = Counter()

updates_needed = []

for bbf_rec in bbf_records:
    es_id = bbf_rec.get("ES_Legacy_ID__c")
    if not es_id or es_id not in es_lookup:
        continue

    stats["matched_to_es"] += 1
    es_rec = es_lookup[es_id]

    update_record = {"Id": bbf_rec["Id"], "fields": {}}

    for bbf_field, es_field in ENRICHMENT_FIELDS.items():
        # Get current BBF value
        if bbf_field == "Loc__c":
            # Geolocation is special
            bbf_lat = bbf_rec.get("Loc__Latitude__s")
            bbf_lng = bbf_rec.get("Loc__Longitude__s")
            bbf_value = (bbf_lat, bbf_lng) if bbf_lat and bbf_lng else None
            es_lat = es_rec.get("Geocode_Lat_Long__Latitude__s")
            es_lng = es_rec.get("Geocode_Lat_Long__Longitude__s")
            es_value = (es_lat, es_lng) if es_lat and es_lng else None
        else:
            bbf_value = bbf_rec.get(bbf_field)
            es_value = es_rec.get(es_field)

        # Track picklist values
        if bbf_field == "Address_Validated_By__c" and es_value:
            verification_values[es_value] += 1
        if bbf_field == "Market__c" and es_value:
            dimension4_values[es_value] += 1

        # Check if enrichment is needed
        if bbf_value:
            # BBF already has value
            stats["fields_already_populated"][bbf_field] += 1
        elif es_value:
            # BBF empty, ES has value -> enrich!
            stats["fields_to_enrich"][bbf_field] += 1

            # Apply transformation if needed
            if bbf_field == "Address_Validated_By__c":
                transformed_value = VERIFICATION_TO_VALIDATED_BY.get(es_value, es_value)
                if transformed_value:
                    update_record["fields"][bbf_field] = {
                        "es_value": es_value,
                        "bbf_value": transformed_value,
                        "note": "Picklist translation",
                    }
            elif bbf_field == "Loc__c":
                update_record["fields"][bbf_field] = {
                    "es_value": f"({es_lat}, {es_lng})",
                    "bbf_value": f"Geolocation({es_lat}, {es_lng})",
                    "note": "Geolocation field",
                }
            else:
                update_record["fields"][bbf_field] = {
                    "es_value": es_value,
                    "bbf_value": es_value,
                    "note": "Direct copy",
                }
        else:
            # Both empty
            stats["es_field_null"][bbf_field] += 1

    if update_record["fields"]:
        update_record["name"] = bbf_rec.get("Name", "N/A")
        updates_needed.append(update_record)

        # Keep sample for display
        if len(stats["sample_updates"]) < 5:
            stats["sample_updates"].append(update_record)

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("DRY RUN RESULTS")
print("=" * 80)

print(f"\nTotal BBF Location__c records:     {stats['total_bbf_records']}")
print(f"Matched to ES Address__c:          {stats['matched_to_es']}")
print(f"Records needing enrichment:        {len(updates_needed)}")

print("\n" + "-" * 80)
print("FIELDS TO ENRICH (BBF empty, ES has value)")
print("-" * 80)
print(f"{'BBF Field':<30} | {'Count':>8} | {'% of Matched':>12}")
print("-" * 80)
for field, count in stats["fields_to_enrich"].most_common():
    pct = count / stats["matched_to_es"] * 100 if stats["matched_to_es"] > 0 else 0
    print(f"{field:<30} | {count:>8} | {pct:>11.1f}%")

print("\n" + "-" * 80)
print("FIELDS ALREADY POPULATED IN BBF")
print("-" * 80)
print(f"{'BBF Field':<30} | {'Count':>8} | {'% of Matched':>12}")
print("-" * 80)
for field, count in stats["fields_already_populated"].most_common():
    pct = count / stats["matched_to_es"] * 100 if stats["matched_to_es"] > 0 else 0
    print(f"{field:<30} | {count:>8} | {pct:>11.1f}%")

print("\n" + "-" * 80)
print("ES FIELDS WITH NULL VALUES (cannot enrich)")
print("-" * 80)
print(f"{'BBF Field <- ES Field':<40} | {'Count':>8} | {'% of Matched':>12}")
print("-" * 80)
for field, count in stats["es_field_null"].most_common():
    es_field = ENRICHMENT_FIELDS[field]
    if isinstance(es_field, tuple):
        es_field = f"{es_field[0]}/{es_field[1]}"
    pct = count / stats["matched_to_es"] * 100 if stats["matched_to_es"] > 0 else 0
    print(f"{field} <- {es_field:<20} | {count:>8} | {pct:>11.1f}%")

print("\n" + "-" * 80)
print("PICKLIST VALUE DISTRIBUTION: Verification_Used__c -> Address_Validated_By__c")
print("-" * 80)
for value, count in verification_values.most_common():
    mapped = VERIFICATION_TO_VALIDATED_BY.get(value, value)
    status = "OK" if mapped else "NEEDS DECISION"
    print(f"  {value:<20} -> {str(mapped):<15} ({count} records) [{status}]")

print("\n" + "-" * 80)
print("PICKLIST VALUE DISTRIBUTION: Dimension_4_Market__c -> Market__c")
print("-" * 80)
for value, count in dimension4_values.most_common(15):
    print(f"  {value:<30} ({count} records)")
if len(dimension4_values) > 15:
    print(f"  ... and {len(dimension4_values) - 15} more values")

print("\n" + "-" * 80)
print("SAMPLE UPDATES (first 5 records)")
print("-" * 80)
for i, update in enumerate(stats["sample_updates"], 1):
    print(f"\n{i}. Location: {update['name']} (Id: {update['Id'][:15]}...)")
    for field, info in update["fields"].items():
        print(f"   {field}:")
        print(f"      ES value:  {info['es_value']}")
        print(f"      BBF value: {info['bbf_value']}")
        print(f"      Note:      {info['note']}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(
    f"""
Total records to update: {len(updates_needed)}
Total field updates:     {sum(len(u['fields']) for u in updates_needed)}

This was a DRY RUN - no changes were made.
To execute the enrichment, create a notebook based on this analysis.
"""
)

# =============================================================================
# OPTIONAL: Export detailed report
# =============================================================================

if len(sys.argv) > 1 and sys.argv[1] == "--export":
    import pandas as pd
    from datetime import datetime

    # Build DataFrame for export
    rows = []
    for update in updates_needed:
        for field, info in update["fields"].items():
            rows.append(
                {
                    "BBF_Id": update["Id"],
                    "Name": update["name"],
                    "BBF_Field": field,
                    "ES_Value": info["es_value"],
                    "BBF_Value": info["bbf_value"],
                    "Note": info["note"],
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        filename = f"./location_enrichment_dry_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\nExported detailed report to: {filename}")

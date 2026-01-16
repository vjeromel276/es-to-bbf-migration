#!/usr/bin/env python3
"""
Generate Off_Net__c field mapping using AI-POWERED SEMANTIC analysis.
Uses telecom off-net/vendor circuit domain knowledge for intelligent matching.
"""

import csv
import json
import sys
from pathlib import Path

# System fields to exclude
SYSTEM_FIELDS = {
    'Id', 'IsDeleted', 'MasterRecordId', 'CreatedDate', 'CreatedById',
    'LastModifiedDate', 'LastModifiedById', 'SystemModstamp', 'LastActivityDate',
    'LastViewedDate', 'LastReferencedDate', 'JigsawContactId', 'Jigsaw',
    'PhotoUrl', 'CleanStatus'
}

# Day 1 migrated fields to exclude
DAY_1_FIELDS = {
    'Name', 'OwnerId', 'Service__c', 'AA_Location__c', 'ZZ_Location__c',
    'ES_Legacy_ID__c', 'BBF_New_Id__c'
}

# Semantic field mappings based on telecom off-net domain knowledge
SEMANTIC_MAPPINGS = {
    # COGS and cost fields (HIGH confidence - exact semantic match)
    'COGS_MRC__c': ('Cost_MRC__c', 'High', 'Cost of Goods Sold monthly recurring cost (exact semantic match)'),
    'COGS_NRC__c': ('Cost_NRC__c', 'High', 'Cost of Goods Sold non-recurring cost (exact semantic match)'),

    # Circuit identifiers (HIGH confidence)
    'Off_Net_Circuit_ID__c': ('Vendor_circuit_Id__c', 'High', 'Vendor circuit identifier (exact semantic match)'),

    # Dates - disconnect and service dates (HIGH confidence)
    'Disconnect_Date__c': ('Disconnect_Date__c', 'High', 'Service disconnect date (exact API name match)'),
    'Off_Net_Service_Due_Date__c': ('Vendor_Due_date__c', 'High', 'Vendor service due date (semantic match)'),
    'Off_Net_Start_Date__c': ('Vendor_Bill_Start_Date__c', 'High', 'Vendor billing start date (semantic match)'),

    # Vendor references (HIGH confidence)
    'Vendor_BAN__c': ('Vendor_Ban__c', 'High', 'Vendor billing account number reference (exact match)'),
    'Vendor_PON__c': ('VendorPON__c', 'High', 'Vendor purchase order number (exact match)'),

    # Disconnect tracking (HIGH confidence)
    'Disconnect_Submitted_Date__c': ('PM_Order_Completed__c', 'High', 'Disconnect submitted date (semantic match)'),
    'Vendor_Order_Issued__c': ('Vendor_Order_Issued__c', 'High', 'Vendor order issued date (exact API name match)'),

    # Contract term (HIGH confidence - picklist)
    'Term__c': ('Term__c', 'High', 'Contract term in months (requires picklist value mapping)'),

    # ETL and disconnect management (HIGH confidence)
    'Approved_ETL_Disconnect_Date__c': ('Approved_ETL_Disconnect_Date__c', 'High', 'ETL approved disconnect date (exact match)'),
    'Disconnect_PON__c': ('Disconnect_PON__c', 'High', 'Disconnect purchase order (exact match to ES field added later)'),
    'ETL_Amount_Approved__c': ('ETL_Amount_Approved__c', 'High', 'ETL amount approved (exact match)'),
    'Future_Disconnect_Date__c': ('Future_Disconnect_Date__c', 'High', 'Future disconnect date (exact match)'),

    # Service status and problem tracking (MEDIUM confidence)
    'Off_Net_Service_Status__c': ('LEC_Order_Status__c', 'Medium', 'Service status picklist (requires value mapping, different labels)'),
    'Off_Net_Problem_Reason_Code__c': ('Off_Net_Problem_Reason_Code__c', 'Medium', 'Problem reason code (exact values, different contexts)'),

    # Dates with semantic uncertainty (MEDIUM confidence)
    'Off_Net_Original_Due_Date__c': ('Vendor_FOC_Received__c', 'Medium', 'FOC date mapping (date type mismatch semantically)'),

    # Circuit ID variations (MEDIUM confidence)
    'Stripped_Circuit_ID__c': ('Stripped_Circuit_ID2__c', 'Medium', 'Stripped circuit ID (different field purposes)'),

    # Provider fields (LOW confidence - reference vs text)
    'Aloc_COGS_Provider__c': ('Off_Net_Vendor__c', 'Low', 'A-Location COGS provider (reference vs text mismatch)'),
    'Zloc_COGS_Provider__c': ('Vendor_Name__c', 'Low', 'Z-Location COGS provider (reference vs text, accounts payable vendor)'),

    # Circuit ID variations (LOW confidence)
    'BBF_Circuit_ID__c': ('Internal_Circuit_Id__c', 'Low', 'BBF circuit ID (textarea truncation needed)'),

    # Demarc and location (LOW confidence)
    'Demarc_Location__c': ('Demarc_Loaction__c', 'Low', 'Demarc location (typo in ES field, requires truncation)'),

    # Order tracking (LOW confidence)
    'Order_Number__c': ('Vendor_Order__c', 'Low', 'Order number text field (similar purpose)'),

    # Notes and additional info (LOW confidence)
    'Additional_Information__c': ('Notes__c', 'Low', 'Additional information text area (semantic match)'),
    'Off_Net_Problem_Reason__c': ('Off_Net_Problem_Reason__c', 'Low', 'Problem reason text (semantic match)'),

    # Review dates (LOW confidence)
    'Review_Requested_Date__c': ('Requested_ETL_Review_Date__c', 'Low', 'Review requested date (semantic match)'),

    # Vendor NNI (LOW confidence - type mismatch)
    'Vendor_NNI__c': ('Vendor_NNI__c', 'Low', 'Vendor NNI reference vs text (type mismatch)'),

    # Product and service type (LOW confidence - complex picklist mapping)
    'Product__c': ('Bandwidth__c', 'Low', 'Large BBF product picklist (471 values) vs ES bandwidth picklist (43 values)'),
    'Service_Type__c': ('Off_Net_Type__c', 'Low', 'Service type picklist (72 values) vs off-net type multipicklist (3 values)'),
}


def load_csv_fields(csv_path):
    """Load fields from CSV export"""
    fields = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fields[row['Field API Name']] = {
                'api_name': row['Field API Name'],
                'label': row['Field Label'],
                'type': row['Field Type'],
                'is_nillable': row['Is Nillable'],
                'is_custom': row['Custom'],
                'picklist_values': row['Picklist Values']
            }
    return fields


def load_picklist_values(csv_path):
    """Load picklist values from detailed CSV"""
    picklists = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            field = row['Field API Name']
            value = row['Picklist Value']
            if field not in picklists:
                picklists[field] = []
            picklists[field].append(value)
    return picklists


def map_picklist_value(es_value, bbf_values):
    """
    Map an ES picklist value to a BBF value.
    Returns: (suggested_value, match_type)
    """
    es_lower = es_value.lower().strip()

    # Exact match (case insensitive)
    for bbf_val in bbf_values:
        if bbf_val.lower().strip() == es_lower:
            return (bbf_val, 'Exact Match')

    # Close match - check for substring or very similar
    for bbf_val in bbf_values:
        bbf_lower = bbf_val.lower().strip()
        # Check if one contains the other
        if es_lower in bbf_lower or bbf_lower in es_lower:
            return (bbf_val, 'Close Match')

    # No match - return all options
    all_values = ' | '.join(bbf_values)
    return (all_values, 'No Match - Select from list')


def generate_mapping():
    """Main function to generate mapping JSON"""
    base_dir = Path(__file__).parent.parent
    exports_dir = base_dir / 'exports'

    # Load ES and BBF fields
    print("Loading ES Off_Net__c fields...")
    es_fields = load_csv_fields(exports_dir / 'es_Off_Net__c_fields_with_picklists.csv')

    print("Loading BBF Off_Net__c fields...")
    bbf_fields = load_csv_fields(exports_dir / 'bbf_Off_Net__c_fields_with_picklists.csv')

    # Load picklist values
    print("Loading ES picklist values...")
    es_picklists = load_picklist_values(exports_dir / 'es_Off_Net__c_picklist_values.csv')

    print("Loading BBF picklist values...")
    bbf_picklists = load_picklist_values(exports_dir / 'bbf_Off_Net__c_picklist_values.csv')

    # Filter out excluded fields
    print("\nFiltering out system and Day 1 fields...")
    excluded_fields = SYSTEM_FIELDS | DAY_1_FIELDS
    bbf_fields_filtered = {
        api: field for api, field in bbf_fields.items()
        if api not in excluded_fields
    }

    print(f"BBF fields after filtering: {len(bbf_fields_filtered)}")
    print(f"ES fields total: {len(es_fields)}")

    # Create field mappings using semantic knowledge
    print("\nPerforming AI-powered semantic field matching...")
    field_mappings = []

    for bbf_api, bbf_field in bbf_fields_filtered.items():
        # Check if we have a semantic mapping
        if bbf_api in SEMANTIC_MAPPINGS:
            es_api, confidence, notes = SEMANTIC_MAPPINGS[bbf_api]

            # Verify ES field exists
            if es_api not in es_fields:
                print(f"WARNING: Semantic mapping references non-existent ES field: {es_api}")
                es_field = None
            else:
                es_field = es_fields[es_api]
        else:
            # No semantic mapping - mark as None
            es_field = None
            confidence = 'None'
            notes = 'No semantic match found in BBF-specific field (likely BBF-only feature)'

        # Determine if transformer needed
        transformer_needed = 'N'
        if es_field:
            # Type mismatch
            if es_field['type'] != bbf_field['type']:
                transformer_needed = 'Y'
                if 'Data type conversion required' not in notes:
                    notes += ' | Data type conversion required'

            # Picklist fields
            if bbf_field['type'] == 'picklist' and es_field['type'] == 'picklist':
                bbf_vals = bbf_picklists.get(bbf_api, [])
                es_vals = es_picklists.get(es_api, [])
                if bbf_vals and es_vals:
                    # Check if all ES values have exact BBF matches
                    all_match = all(
                        any(ev.lower() == bv.lower() for bv in bbf_vals)
                        for ev in es_vals
                    )
                    if not all_match:
                        transformer_needed = 'Y'
                        if 'Picklist value mapping required' not in notes:
                            notes += ' | Picklist value mapping required'

        mapping = {
            'bbf_field_api': bbf_field['api_name'],
            'bbf_label': bbf_field['label'],
            'bbf_type': bbf_field['type'],
            'bbf_required': 'No' if bbf_field['is_nillable'] == 'True' else 'Yes',
            'es_field_api': es_field['api_name'] if es_field else '',
            'es_label': es_field['label'] if es_field else '',
            'es_type': es_field['type'] if es_field else '',
            'confidence': confidence,
            'transformer_needed': transformer_needed,
            'notes': notes
        }
        field_mappings.append(mapping)

    # Create picklist mappings
    print("\nMapping picklist values...")
    picklist_mappings = []

    # Find picklist fields that matched
    for field_map in field_mappings:
        if field_map['bbf_type'] == 'picklist' and field_map['es_field_api']:
            bbf_field = field_map['bbf_field_api']
            es_field = field_map['es_field_api']

            bbf_vals = bbf_picklists.get(bbf_field, [])
            es_vals = es_picklists.get(es_field, [])

            if bbf_vals and es_vals:
                for es_val in es_vals:
                    suggested, match_type = map_picklist_value(es_val, bbf_vals)
                    picklist_mappings.append({
                        'es_field': es_field,
                        'es_value': es_val,
                        'bbf_field': bbf_field,
                        'suggested_mapping': suggested,
                        'notes': match_type,
                        'bbf_final_value': ''
                    })

    # Create JSON output
    output_data = {
        'field_mappings': field_mappings,
        'picklist_mappings': picklist_mappings
    }

    output_path = exports_dir / 'off_net_mapping.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMapping JSON created: {output_path}")
    print(f"Total field mappings: {len(field_mappings)}")
    print(f"Total picklist mappings: {len(picklist_mappings)}")

    # Statistics
    high_conf = sum(1 for m in field_mappings if m['confidence'] == 'High')
    medium_conf = sum(1 for m in field_mappings if m['confidence'] == 'Medium')
    low_conf = sum(1 for m in field_mappings if m['confidence'] == 'Low')
    none_conf = sum(1 for m in field_mappings if m['confidence'] == 'None')

    print(f"\nConfidence Breakdown:")
    print(f"  High: {high_conf}")
    print(f"  Medium: {medium_conf}")
    print(f"  Low: {low_conf}")
    print(f"  None: {none_conf}")

    return output_path


if __name__ == '__main__':
    try:
        output_path = generate_mapping()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

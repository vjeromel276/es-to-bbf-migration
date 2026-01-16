#!/usr/bin/env python3
"""
Semantic mapping for ES OrderItem to BBF Service_Charge__c.
Uses AI-powered semantic matching based on billing/charge domain knowledge.
"""

import csv
import json
import sys
from pathlib import Path
from difflib import SequenceMatcher

# System fields to exclude
SYSTEM_FIELDS = {
    'Id', 'IsDeleted', 'MasterRecordId', 'CreatedDate', 'CreatedById',
    'LastModifiedDate', 'LastModifiedById', 'SystemModstamp', 'LastActivityDate',
    'LastViewedDate', 'LastReferencedDate', 'JigsawContactId', 'Jigsaw',
    'PhotoUrl', 'CleanStatus'
}

# Day 1 migration fields for Service_Charge__c (already populated)
DAY1_FIELDS_SERVICE_CHARGE = {
    'Name', 'Service__c', 'Product_Simple__c', 'Service_Type_Charge__c',
    'ES_Legacy_ID__c', 'BBF_New_Id__c'
}


def similarity_ratio(s1, s2):
    """Calculate similarity ratio between two strings (case insensitive)."""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def normalize_field_name(field_name):
    """Normalize field name for comparison - remove common prefixes/suffixes."""
    normalized = field_name.replace('__c', '').replace('_', ' ').lower()
    # Remove common prefixes
    for prefix in ['sbqq', 'hidden']:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    return normalized


def semantic_match_fields(bbf_field, es_fields_data):
    """
    Semantically match a BBF field to the best ES field.
    Returns: (es_field_api, es_label, es_type, confidence, notes)
    """
    bbf_api = bbf_field['Field API Name']
    bbf_label = bbf_field['Field Label']
    bbf_type = bbf_field['Field Type']

    # Billing/charge domain semantic mappings
    semantic_rules = {
        # Core charge fields
        'Unit_Rate__c': {
            'matches': ['UnitPrice', 'UnitPriceForceOverride__c'],
            'confidence': 'High',
            'notes': 'Unit rate for the charge - maps to OrderItem UnitPrice'
        },
        'Units__c': {
            'matches': ['Quantity', 'QTY__c'],
            'confidence': 'High',
            'notes': 'Quantity of units - maps to OrderItem Quantity'
        },
        'Start_Date__c': {
            'matches': ['ServiceDate', 'Contract_End_Month__c'],
            'confidence': 'High',
            'notes': 'Service start date - maps to OrderItem ServiceDate'
        },
        'End_Date__c': {
            'matches': ['EndDate', 'Contract_End_Month__c', 'Estimated_Service_Expiration_Date__c'],
            'confidence': 'High',
            'notes': 'Service end date - maps to OrderItem EndDate'
        },
        'Description__c': {
            'matches': ['Description', 'Item_Summary__c', 'Imported_Description__c'],
            'confidence': 'High',
            'notes': 'Charge description - maps to OrderItem Description or Item_Summary__c'
        },
        'NRC__c': {
            'matches': ['NRC_IRU_FEE__c', 'NRC_Non_Amortized__c', 'Total_NRC_Non_Amortized_ROLLUP__c', 'Vendor_NRC__c'],
            'confidence': 'High',
            'notes': 'Non-recurring charge - maps to OrderItem NRC fields'
        },
        'MRC_COGS__c': {
            'matches': ['Vendor_Fees_Monthly__c'],
            'confidence': 'High',
            'notes': 'Monthly recurring COGS - maps to OrderItem Vendor_Fees_Monthly__c'
        },
        'NRC_COGS__c': {
            'matches': ['Vendor_NRC__c'],
            'confidence': 'High',
            'notes': 'Non-recurring COGS - maps to OrderItem Vendor_NRC__c'
        },
        # Billing configuration
        'Charge_Class__c': {
            'matches': ['SBQQ__ChargeType__c', 'SBQQ__BillingType__c'],
            'confidence': 'Medium',
            'notes': 'Charge classification (RECUR/NONRECUR) - derive from SBQQ__ChargeType__c (Recurring=RECUR, One-Time=NONRECUR)'
        },
        'Bill_Schedule_Type__c': {
            'matches': ['SBQQ__BillingFrequency__c'],
            'confidence': 'Medium',
            'notes': 'Billing schedule type - derive from SBQQ__BillingFrequency__c'
        },
        'Charge_Active__c': {
            'matches': ['SBQQ__Activated__c', 'Cancelled__c'],
            'confidence': 'Medium',
            'notes': 'Whether charge is active - derive from SBQQ__Activated__c and !Cancelled__c'
        },
        # Reference fields
        'Service_Order_Line_Charge__c': {
            'matches': ['SBQQ__QuoteLine__c', 'Quote_Line_Item_ID__c'],
            'confidence': 'Low',
            'notes': 'Reference to originating quote line - may map to SBQQ__QuoteLine__c if needed'
        },
        'Off_Net__c': {
            'matches': ['OFF_NET_IDs__c'],
            'confidence': 'Medium',
            'notes': 'Off-Net relationship - derive from OrderItem OFF_NET_IDs__c field'
        },
        # Tax/fee related
        'PricebookEntryId__c': {
            'matches': ['PricebookEntryId'],
            'confidence': 'High',
            'notes': 'Pricebook entry reference - direct match to OrderItem.PricebookEntryId'
        },
        # Dates for billing tracking
        'Start_Date_Achieved_On__c': {
            'matches': ['ServiceDate'],
            'confidence': 'Low',
            'notes': 'Date when start date was achieved - may track when ServiceDate was set'
        },
        'End_Date_Achieved_On__c': {
            'matches': ['EndDate'],
            'confidence': 'Low',
            'notes': 'Date when end date was achieved - may track when EndDate was set'
        },
        # Migration tracking
        'Disabled_COPS_Synchronization__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific field for COPS sync control - no ES equivalent'
        },
        'Ignore_in_MBB_Billing_Manually__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific billing control - no ES equivalent'
        },
        'Ignore_in_MBB_Billing_Calculated__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific billing control - no ES equivalent'
        },
        'Ignore_in_MBB_Billing_Backbill_Not_Found__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific billing control - no ES equivalent'
        },
        'Ignore_in_MBB_Billing_Infra_Calc__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific billing control - no ES equivalent'
        },
        'Do_Not_Backbill__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF-specific billing control - no ES equivalent'
        },
        'Aloc_COGS_Provider__c': {
            'matches': ['Last_Mile_Carrier__c'],
            'confidence': 'Low',
            'notes': 'A-location COGS provider - may derive from Last_Mile_Carrier__c if location-specific'
        },
        'Zloc_COGS_Provider__c': {
            'matches': ['Last_Mile_Carrier__c'],
            'confidence': 'Low',
            'notes': 'Z-location COGS provider - may derive from Last_Mile_Carrier__c if location-specific'
        },
        # Price escalation
        'Exclude_From_Escalation__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Price escalation control - no ES equivalent'
        },
        'Next_Price_Escalation__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Next escalation date - no ES equivalent'
        },
        'Escalation_Notes__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Escalation notes - no ES equivalent'
        },
        'Escalation_Created_Charge__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Flag for escalation-created charges - no ES equivalent'
        },
        'Price_Increase__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Price increase flag - no ES equivalent'
        },
        # Calculated/formula fields
        'Amount__c': {
            'matches': ['Total_MRC_Amortized__c', 'TotalPrice'],
            'confidence': 'High',
            'notes': 'MRC amount (calculated as Unit_Rate__c * Units__c) - maps to Total_MRC_Amortized__c'
        },
        'MRC_Net__c': {
            'matches': ['Total_MRC_Amortized__c', 'Net_Margin__c'],
            'confidence': 'Medium',
            'notes': 'Net MRC (formula field) - calculate from OrderItem pricing'
        },
        'NRC_Net__c': {
            'matches': ['NRC_Non_Amortized__c', 'Total_NRC_Non_Amortized_ROLLUP__c'],
            'confidence': 'Medium',
            'notes': 'Net NRC (formula field) - calculate from OrderItem NRC fields'
        },
        'Active__c': {
            'matches': ['SBQQ__Activated__c', 'Cancelled__c'],
            'confidence': 'Medium',
            'notes': 'Active status (formula field) - derive from SBQQ__Activated__c and !Cancelled__c'
        },
        'Private_Line_YN__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Private line indicator (formula) - BBF-specific logic'
        },
        'Start_Date_Day__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Day of month from start date (formula) - BBF-specific'
        },
        'End_Date_Day__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Day of month from end date (formula) - BBF-specific'
        },
        # Deprecated fields
        'Charge__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Deprecated charge type reference - not used in migration'
        },
        'Product_Category__c': {
            'matches': ['Product_Family__c'],
            'confidence': 'Low',
            'notes': 'Deprecated product category (formula) - may derive from Product_Family__c'
        },
        'Product_Name__c': {
            'matches': ['Product_Name__c'],
            'confidence': 'Low',
            'notes': 'Deprecated product name (formula) - direct match if needed'
        },
        'Product__c': {
            'matches': ['Product2Id'],
            'confidence': 'Low',
            'notes': 'Deprecated product reference - maps to Product2Id'
        },
        'Test_Formula__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Test formula field - not used in migration'
        },
        # Metadata fields
        'Sequence__c': {
            'matches': ['OrderItemNumber'],
            'confidence': 'Medium',
            'notes': 'Sequence or line number - maps to OrderItemNumber'
        },
        'Match_Key__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF matching key - generate from OrderItem.Id or unique combination'
        },
        'Unified_DB_Last_Synced_Date__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'BBF sync timestamp - not applicable for migration'
        },
        'SC_Record_Type__c': {
            'matches': [],
            'confidence': 'None',
            'notes': 'Service Charge record type (Charge vs COGS) - set based on charge nature'
        },
    }

    # Check if we have a semantic rule for this field
    if bbf_api in semantic_rules:
        rule = semantic_rules[bbf_api]
        matches = rule['matches']
        confidence = rule['confidence']
        notes = rule['notes']

        if not matches:
            return ('', '', '', 'None', notes)

        # Return first match from the rule
        for match in matches:
            for es_field in es_fields_data:
                if es_field['Field API Name'] == match:
                    return (
                        es_field['Field API Name'],
                        es_field['Field Label'],
                        es_field['Field Type'],
                        confidence,
                        notes
                    )

        # If no exact match found, return empty with note
        return ('', '', '', confidence, notes)

    # Fallback: try API name and label similarity matching
    best_match = None
    best_score = 0.0

    bbf_norm = normalize_field_name(bbf_api)

    for es_field in es_fields_data:
        es_api = es_field['Field API Name']
        es_label = es_field['Field Label']
        es_type = es_field['Field Type']

        # Skip system fields
        if es_api in SYSTEM_FIELDS:
            continue

        # Calculate similarity scores
        api_score = similarity_ratio(bbf_api, es_api)
        label_score = similarity_ratio(bbf_label, es_label)
        norm_score = similarity_ratio(bbf_norm, normalize_field_name(es_api))

        # Combined score (weighted)
        combined_score = max(api_score * 1.5, label_score, norm_score)

        if combined_score > best_score:
            best_score = combined_score
            best_match = (es_api, es_label, es_type)

    # Determine confidence based on score
    if best_score >= 0.8:
        confidence = 'High'
        notes = f'High similarity match (score: {best_score:.2f})'
    elif best_score >= 0.5:
        confidence = 'Medium'
        notes = f'Moderate similarity match (score: {best_score:.2f}) - verify mapping'
    elif best_score >= 0.3:
        confidence = 'Low'
        notes = f'Low similarity match (score: {best_score:.2f}) - likely needs manual review'
    else:
        confidence = 'None'
        notes = 'No reasonable match found - manual mapping required'
        best_match = None

    if best_match:
        return (best_match[0], best_match[1], best_match[2], confidence, notes)
    else:
        return ('', '', '', 'None', notes)


def match_picklist_values(es_field, es_values, bbf_field, bbf_values):
    """
    Match picklist values between ES and BBF fields.
    Returns list of picklist mapping dicts.
    """
    mappings = []

    # Parse BBF values into a set
    bbf_value_set = set()
    if bbf_values:
        for val in bbf_values.split('; '):
            bbf_value_set.add(val.strip())

    # Parse ES values
    es_value_list = []
    if es_values:
        for val in es_values.split('; '):
            es_value_list.append(val.strip())

    for es_val in es_value_list:
        # Try exact match
        if es_val in bbf_value_set:
            mappings.append({
                'es_field': es_field,
                'es_value': es_val,
                'bbf_field': bbf_field,
                'suggested_mapping': es_val,
                'notes': 'Exact Match',
                'bbf_final_value': ''
            })
        else:
            # Try fuzzy match
            best_match = None
            best_score = 0.0

            for bbf_val in bbf_value_set:
                score = similarity_ratio(es_val, bbf_val)
                if score > best_score:
                    best_score = score
                    best_match = bbf_val

            if best_score >= 0.7:
                mappings.append({
                    'es_field': es_field,
                    'es_value': es_val,
                    'bbf_field': bbf_field,
                    'suggested_mapping': best_match,
                    'notes': 'Close Match',
                    'bbf_final_value': ''
                })
            else:
                # No match - list all BBF values
                all_bbf_values = ' | '.join(sorted(bbf_value_set))
                mappings.append({
                    'es_field': es_field,
                    'es_value': es_val,
                    'bbf_field': bbf_field,
                    'suggested_mapping': all_bbf_values,
                    'notes': 'No Match - Select from list',
                    'bbf_final_value': ''
                })

    return mappings


def main():
    # File paths
    base_dir = Path(__file__).parent.parent
    exports_dir = base_dir / 'exports'
    mappings_dir = base_dir / 'mappings'

    es_fields_file = exports_dir / 'es_OrderItem_fields_with_picklists.csv'
    bbf_fields_file = exports_dir / 'bbf_Service_Charge__c_fields_with_picklists.csv'

    # Read ES fields
    print("Reading ES OrderItem fields...")
    es_fields = []
    with open(es_fields_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            es_fields.append(row)
    print(f"Loaded {len(es_fields)} ES fields")

    # Read BBF fields
    print("Reading BBF Service_Charge__c fields...")
    bbf_fields = []
    with open(bbf_fields_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Exclude system fields and Day 1 fields
            field_api = row['Field API Name']
            if field_api not in SYSTEM_FIELDS and field_api not in DAY1_FIELDS_SERVICE_CHARGE:
                bbf_fields.append(row)
    print(f"Loaded {len(bbf_fields)} BBF fields (after filtering)")

    # Create field mappings
    print("\nCreating field mappings...")
    field_mappings = []
    picklist_mappings = []

    for bbf_field in bbf_fields:
        bbf_api = bbf_field['Field API Name']
        bbf_label = bbf_field['Field Label']
        bbf_type = bbf_field['Field Type']
        bbf_required = 'Yes' if bbf_field.get('Is Nillable', 'True') == 'False' else 'No'

        # Find semantic match
        es_api, es_label, es_type, confidence, notes = semantic_match_fields(bbf_field, es_fields)

        # Determine if transformer is needed
        transformer_needed = 'N'
        if confidence in ['Medium', 'Low'] and es_api:
            transformer_needed = 'Y'
        if es_type and bbf_type and es_type != bbf_type:
            transformer_needed = 'Y'
        if 'derive' in notes.lower() or 'calculate' in notes.lower() or 'transform' in notes.lower():
            transformer_needed = 'Y'

        field_mappings.append({
            'bbf_field_api': bbf_api,
            'bbf_label': bbf_label,
            'bbf_type': bbf_type,
            'bbf_required': bbf_required,
            'es_field_api': es_api,
            'es_label': es_label,
            'es_type': es_type,
            'confidence': confidence,
            'transformer_needed': transformer_needed,
            'notes': notes
        })

        # Handle picklist mappings
        if bbf_type == 'picklist' and es_api:
            # Find ES field data
            es_field_data = None
            for esf in es_fields:
                if esf['Field API Name'] == es_api:
                    es_field_data = esf
                    break

            if es_field_data and es_field_data.get('Field Type') == 'picklist':
                es_values = es_field_data.get('Picklist Values', '')
                bbf_values = bbf_field.get('Picklist Values', '')

                if es_values and bbf_values:
                    pl_maps = match_picklist_values(es_api, es_values, bbf_api, bbf_values)
                    picklist_mappings.extend(pl_maps)

    # Create JSON output
    output_data = {
        'field_mappings': field_mappings,
        'picklist_mappings': picklist_mappings
    }

    # Save JSON
    json_file = exports_dir / 'orderitem_servicecharge_mapping.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nMapping JSON created: {json_file}")
    print(f"  Field mappings: {len(field_mappings)}")
    print(f"  Picklist mappings: {len(picklist_mappings)}")

    # Print statistics
    high = sum(1 for m in field_mappings if m['confidence'] == 'High')
    medium = sum(1 for m in field_mappings if m['confidence'] == 'Medium')
    low = sum(1 for m in field_mappings if m['confidence'] == 'Low')
    none = sum(1 for m in field_mappings if m['confidence'] == 'None')
    transformers = sum(1 for m in field_mappings if m['transformer_needed'] == 'Y')

    print(f"\nConfidence breakdown:")
    print(f"  High: {high}")
    print(f"  Medium: {medium}")
    print(f"  Low: {low}")
    print(f"  None: {none}")
    print(f"  Transformers needed: {transformers}")


if __name__ == '__main__':
    main()

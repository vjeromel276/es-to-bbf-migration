#!/usr/bin/env python3
"""
Generate Off_Net__c field mapping using semantic analysis.
Analyzes ES and BBF Off_Net__c fields and creates JSON mapping data.
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

# Day 1 migrated fields to exclude
DAY_1_FIELDS = {
    'Name', 'OwnerId', 'Service__c', 'AA_Location__c', 'ZZ_Location__c',
    'ES_Legacy_ID__c', 'BBF_New_Id__c'
}


def similarity_score(str1, str2):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def normalize_api_name(api_name):
    """Normalize API name for comparison (remove __c, lowercase)"""
    return api_name.replace('__c', '').lower()


def load_csv_fields(csv_path):
    """Load fields from CSV export"""
    fields = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fields.append({
                'api_name': row['Field API Name'],
                'label': row['Field Label'],
                'type': row['Field Type'],
                'is_nillable': row['Is Nillable'],
                'is_custom': row['Custom'],
                'picklist_values': row['Picklist Values']
            })
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


def match_field(bbf_field, es_fields):
    """
    Semantically match a BBF field to an ES field.
    Returns: (es_field, confidence, notes)
    """
    bbf_api = bbf_field['api_name']
    bbf_label = bbf_field['label']
    bbf_norm = normalize_api_name(bbf_api)

    best_match = None
    best_score = 0
    match_reason = ""

    for es_field in es_fields:
        es_api = es_field['api_name']
        es_norm = normalize_api_name(es_api)

        # Exact API name match
        if bbf_norm == es_norm:
            return (es_field, 'High', 'Exact API name match')

        # API name similarity
        api_sim = similarity_score(bbf_norm, es_norm)
        if api_sim > best_score:
            best_score = api_sim
            best_match = es_field
            match_reason = f"API name similarity ({api_sim:.2f})"

        # Label similarity
        label_sim = similarity_score(bbf_label.lower(), es_field['label'].lower())
        if label_sim > 0.8 and label_sim > best_score:
            best_score = label_sim
            best_match = es_field
            match_reason = f"Label similarity ({label_sim:.2f})"

    # Determine confidence based on score
    if best_score >= 0.9:
        confidence = 'High'
    elif best_score >= 0.7:
        confidence = 'Medium'
    elif best_score >= 0.5:
        confidence = 'Low'
    else:
        confidence = 'None'
        return (None, confidence, 'No semantic match found')

    return (best_match, confidence, match_reason)


def map_picklist_value(es_value, bbf_values):
    """
    Map an ES picklist value to a BBF value.
    Returns: (suggested_value, match_type)
    """
    es_lower = es_value.lower().strip()

    # Exact match
    for bbf_val in bbf_values:
        if bbf_val.lower().strip() == es_lower:
            return (bbf_val, 'Exact Match')

    # Close match (high similarity)
    best_match = None
    best_score = 0
    for bbf_val in bbf_values:
        score = similarity_score(es_lower, bbf_val.lower())
        if score > best_score:
            best_score = score
            best_match = bbf_val

    if best_score >= 0.8:
        return (best_match, 'Close Match')

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
    bbf_fields_filtered = [
        f for f in bbf_fields
        if f['api_name'] not in excluded_fields
    ]
    es_fields_filtered = [
        f for f in es_fields
        if f['api_name'] not in excluded_fields
    ]

    print(f"BBF fields after filtering: {len(bbf_fields_filtered)}")
    print(f"ES fields after filtering: {len(es_fields_filtered)}")

    # Create field mappings
    print("\nPerforming semantic field matching...")
    field_mappings = []

    for bbf_field in bbf_fields_filtered:
        es_field, confidence, notes = match_field(bbf_field, es_fields_filtered)

        # Determine if transformer needed
        transformer_needed = 'N'
        if es_field:
            # Type mismatch
            if es_field['type'] != bbf_field['type']:
                transformer_needed = 'Y'
                notes += ' | Data type conversion required'

            # Picklist fields
            if bbf_field['type'] == 'picklist' and es_field['type'] == 'picklist':
                bbf_vals = bbf_picklists.get(bbf_field['api_name'], [])
                es_vals = es_picklists.get(es_field['api_name'], [])
                if bbf_vals and es_vals:
                    # Check if all ES values have exact BBF matches
                    all_match = all(
                        any(ev.lower() == bv.lower() for bv in bbf_vals)
                        for ev in es_vals
                    )
                    if not all_match:
                        transformer_needed = 'Y'
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

#!/usr/bin/env python3
"""
Mapping Reader Utility
======================
Reads Day Two field mapping Excel files and returns field mappings
and picklist translations for enrichment notebooks.

Usage:
    from mapping_reader import load_mapping

    mapping = load_mapping('ES_Address__c_to_BBF_Location__c_mapping.xlsx')

    # Get field mappings (BBF field -> ES field)
    field_map = mapping['field_mappings']

    # Get picklist translations (ES value -> BBF value)
    picklist_map = mapping['picklist_mappings']

    # Get fields that need enrichment (have ES source and confidence >= Medium)
    enrichable = mapping['enrichable_fields']
"""

import pandas as pd
import os
from typing import Dict, List, Any, Optional

# Default mapping directory
MAPPING_DIR = os.path.join(os.path.dirname(__file__), 'mappings')


def load_mapping(filename: str, mapping_dir: str = None) -> Dict[str, Any]:
    """
    Load a field mapping Excel file and return structured data.

    Args:
        filename: Name of the mapping Excel file (e.g., 'ES_Address__c_to_BBF_Location__c_mapping.xlsx')
        mapping_dir: Optional directory path (defaults to day-two/mappings/)

    Returns:
        Dictionary with:
        - field_mappings: Dict[BBF_field, ES_field]
        - picklist_mappings: Dict[BBF_field, Dict[ES_value, BBF_value]]
        - enrichable_fields: List of BBF fields that can be enriched
        - all_fields: Full DataFrame of field mapping sheet
    """
    if mapping_dir is None:
        mapping_dir = MAPPING_DIR

    filepath = os.path.join(mapping_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Mapping file not found: {filepath}")

    result = {
        'filename': filename,
        'filepath': filepath,
        'field_mappings': {},
        'picklist_mappings': {},
        'enrichable_fields': [],
        'all_fields': None,
        'all_picklists': None,
    }

    # Read Field_Mapping sheet
    try:
        df_fields = pd.read_excel(filepath, sheet_name='Field_Mapping')
        result['all_fields'] = df_fields

        # Build field mapping dictionary
        for _, row in df_fields.iterrows():
            bbf_field = row.get('BBF_Field_API_Name') or row.get('BBF Field API Name')
            es_field = row.get('ES_Field_API_Name') or row.get('ES Field API Name')
            confidence = row.get('Match_Confidence') or row.get('Confidence') or ''

            if pd.notna(bbf_field) and pd.notna(es_field) and str(es_field).strip():
                result['field_mappings'][bbf_field] = es_field

                # Get field label for deprecated check
                bbf_label = row.get('BBF_Field_Label') or row.get('BBF Field Label') or ''

                # Track enrichable fields (have source and reasonable confidence)
                # Skip deprecated fields (label contains "(dep)")
                # Skip fields marked Include_in_Migration = 'No'
                conf_str = str(confidence).lower()
                is_deprecated = '(dep)' in str(bbf_label).lower()

                # Check Include_in_Migration column (default to Yes if missing)
                include_in_migration = str(row.get('Include_in_Migration', 'Yes')).strip().lower()
                should_include = include_in_migration in ['yes', 'y', '']

                if conf_str in ['high', 'medium', 'exact', 'semantic'] and not is_deprecated and should_include:
                    result['enrichable_fields'].append({
                        'bbf_field': bbf_field,
                        'es_field': es_field,
                        'confidence': confidence,
                        'transformer_needed': row.get('Transformer_Needed', 'N') == 'Y',
                        'bbf_label': bbf_label
                    })
    except Exception as e:
        print(f"Warning: Could not read Field_Mapping sheet: {e}")

    # Read Picklist_Mapping sheet
    try:
        df_picklists = pd.read_excel(filepath, sheet_name='Picklist_Mapping')
        result['all_picklists'] = df_picklists

        # Build picklist mapping dictionary
        for _, row in df_picklists.iterrows():
            bbf_field = row.get('BBF_Field') or row.get('BBF Field')
            es_value = row.get('ES_Picklist_Value') or row.get('ES Value') or row.get('ES_Value')
            bbf_value = row.get('BBF_Final_Value') or row.get('Suggested_Mapping') or row.get('BBF Value')

            if pd.notna(bbf_field) and pd.notna(es_value):
                if bbf_field not in result['picklist_mappings']:
                    result['picklist_mappings'][bbf_field] = {}

                # Only add if we have a definite BBF value (not a list of options)
                if pd.notna(bbf_value) and '|' not in str(bbf_value):
                    result['picklist_mappings'][bbf_field][str(es_value)] = str(bbf_value).strip()
    except Exception as e:
        print(f"Warning: Could not read Picklist_Mapping sheet: {e}")

    return result


def is_deprecated_field(field_label: str) -> bool:
    """
    Check if a field is deprecated based on its label.

    Args:
        field_label: The BBF field label to check

    Returns:
        True if the field label contains "(dep)" (case-insensitive)
    """
    return '(dep)' in str(field_label).lower()


def get_enrichment_fields(mapping: Dict, exclude_day1_fields: List[str] = None,
                          include_deprecated: bool = False) -> Dict[str, str]:
    """
    Get fields that should be enriched (have ES source, not Day 1 fields).

    Args:
        mapping: Result from load_mapping()
        exclude_day1_fields: List of BBF field names that were migrated on Day 1
        include_deprecated: If True, include deprecated fields (default: False)

    Returns:
        Dictionary of BBF_field -> ES_field for enrichment
    """
    if exclude_day1_fields is None:
        exclude_day1_fields = []

    # Common Day 1 / system fields to exclude
    default_exclude = [
        'Id', 'Name', 'OwnerId', 'ES_Legacy_ID__c', 'RecordTypeId',
        'CreatedDate', 'CreatedById', 'LastModifiedDate', 'LastModifiedById',
        'IsDeleted', 'SystemModstamp'
    ]

    all_exclude = set(default_exclude + exclude_day1_fields)

    enrichment_fields = {}
    for item in mapping.get('enrichable_fields', []):
        bbf_field = item['bbf_field']
        bbf_label = item.get('bbf_label', '')

        # Skip excluded fields
        if bbf_field in all_exclude:
            continue

        # Skip deprecated fields unless explicitly included
        if not include_deprecated and is_deprecated_field(bbf_label):
            continue

        enrichment_fields[bbf_field] = item['es_field']

    return enrichment_fields


def translate_picklist(mapping: Dict, bbf_field: str, es_value: Any) -> Optional[str]:
    """
    Translate an ES picklist value to BBF using the mapping.

    Args:
        mapping: Result from load_mapping()
        bbf_field: The BBF field name
        es_value: The ES value to translate

    Returns:
        Translated BBF value, or original value if no translation found
    """
    if es_value is None:
        return None

    picklist_map = mapping.get('picklist_mappings', {}).get(bbf_field, {})
    es_str = str(es_value).strip()

    return picklist_map.get(es_str, es_str)


def get_deprecated_fields(mapping: Dict) -> List[Dict]:
    """
    Get list of deprecated fields that were excluded from enrichment.

    Args:
        mapping: Result from load_mapping()

    Returns:
        List of deprecated field info dicts
    """
    deprecated = []
    df_fields = mapping.get('all_fields')
    if df_fields is None:
        return deprecated

    for _, row in df_fields.iterrows():
        bbf_label = row.get('BBF_Field_Label') or row.get('BBF Field Label') or ''
        if is_deprecated_field(bbf_label):
            deprecated.append({
                'bbf_field': row.get('BBF_Field_API_Name') or row.get('BBF Field API Name'),
                'bbf_label': bbf_label,
                'es_field': row.get('ES_Field_API_Name') or row.get('ES Field API Name')
            })
    return deprecated


def print_mapping_summary(mapping: Dict, show_deprecated: bool = True):
    """Print a summary of the loaded mapping."""
    print(f"\n{'='*60}")
    print(f"Mapping: {mapping['filename']}")
    print(f"{'='*60}")
    print(f"Total field mappings: {len(mapping['field_mappings'])}")
    print(f"Enrichable fields: {len(mapping['enrichable_fields'])}")
    print(f"Picklist fields with translations: {len(mapping['picklist_mappings'])}")

    # Show deprecated fields that were excluded
    deprecated = get_deprecated_fields(mapping)
    if deprecated and show_deprecated:
        print(f"\nDeprecated fields excluded: {len(deprecated)}")
        for item in deprecated:
            print(f"  [DEP] {item['bbf_field']:<30} ({item['bbf_label']})")

    if mapping['enrichable_fields']:
        print(f"\nEnrichable Fields:")
        for item in mapping['enrichable_fields'][:10]:
            transformer = " [T]" if item['transformer_needed'] else ""
            print(f"  {item['bbf_field']:<35} <- {item['es_field']:<30} ({item['confidence']}){transformer}")
        if len(mapping['enrichable_fields']) > 10:
            print(f"  ... and {len(mapping['enrichable_fields']) - 10} more")

    if mapping['picklist_mappings']:
        print(f"\nPicklist Translations:")
        for field, translations in list(mapping['picklist_mappings'].items())[:3]:
            print(f"  {field}:")
            for es_val, bbf_val in list(translations.items())[:3]:
                print(f"    {es_val} -> {bbf_val}")
            if len(translations) > 3:
                print(f"    ... and {len(translations) - 3} more")


# Convenience function to load all mappings
MAPPING_FILES = {
    'location': 'ES_Address__c_to_BBF_Location__c_mapping.xlsx',
    'account': 'ES_Account_to_BBF_Account_mapping.xlsx',
    'contact': 'ES_Contact_to_BBF_Contact_mapping.xlsx',
    'ban': 'ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx',
    'service': 'ES_Order_to_BBF_Service__c_mapping.xlsx',
    'service_charge': 'ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx',
    'offnet': 'ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx',
}


def load_all_mappings() -> Dict[str, Dict]:
    """Load all mapping files."""
    mappings = {}
    for key, filename in MAPPING_FILES.items():
        try:
            mappings[key] = load_mapping(filename)
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
    return mappings


if __name__ == '__main__':
    # Test loading a mapping
    print("Testing mapping reader...")

    for name, filename in MAPPING_FILES.items():
        try:
            mapping = load_mapping(filename)
            print_mapping_summary(mapping)
        except FileNotFoundError:
            print(f"\n⚠️  {filename} not found")
        except Exception as e:
            print(f"\n❌ Error loading {filename}: {e}")

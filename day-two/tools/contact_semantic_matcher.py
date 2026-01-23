#!/usr/bin/env python3
"""
AI-Powered Semantic Field Matching for ES Contact to BBF Contact
Uses domain knowledge and semantic understanding instead of fuzzy string matching.
"""

import csv
import json
import sys
from typing import Dict, List, Tuple, Optional

# Day 1 fields to exclude (already migrated)
DAY_1_FIELDS = {
    'FirstName', 'LastName', 'Name', 'AccountId', 'OwnerId',
    'ES_Legacy_ID__c', 'BBF_New_Id__c', 'Email', 'Phone'
}

# System fields to exclude
SYSTEM_FIELDS = {
    'Id', 'IsDeleted', 'MasterRecordId', 'CreatedDate', 'CreatedById',
    'LastModifiedDate', 'LastModifiedById', 'SystemModstamp',
    'LastActivityDate', 'LastViewedDate', 'LastReferencedDate',
    'JigsawContactId', 'Jigsaw', 'PhotoUrl'
}


def load_fields(csv_path: str) -> List[Dict]:
    """Load field metadata from CSV"""
    fields = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fields.append(row)
    return fields


def load_picklist_values(csv_path: str) -> Dict[str, List[str]]:
    """Load picklist values grouped by field"""
    picklist_map = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            field_api = row['Field API Name']
            value = row['Picklist Value']
            if field_api not in picklist_map:
                picklist_map[field_api] = []
            picklist_map[field_api].append(value)
    return picklist_map


def semantic_match_contact_field(bbf_field: Dict, es_fields: List[Dict]) -> Tuple[Optional[Dict], str, str, bool]:
    """
    Perform AI-powered semantic matching for a BBF Contact field.
    Returns: (matched_es_field, confidence, notes, needs_transformer)

    Uses CRM/contact domain knowledge to intelligently match fields.
    """
    bbf_api = bbf_field['Field API Name']
    bbf_label = bbf_field['Field Label']
    bbf_type = bbf_field['Field Type']

    # EXACT API NAME MATCHES (High Confidence)
    exact_matches = {
        'Salutation': 'Salutation',
        'MiddleName': None,  # ES doesn't have MiddleName
        'Suffix': None,  # ES doesn't have Suffix
        'OtherStreet': 'OtherStreet',
        'OtherCity': 'OtherCity',
        'OtherState': 'OtherState',
        'OtherPostalCode': 'OtherPostalCode',
        'OtherCountry': 'OtherCountry',
        'OtherLatitude': 'OtherLatitude',
        'OtherLongitude': 'OtherLongitude',
        'OtherGeocodeAccuracy': 'OtherGeocodeAccuracy',
        'OtherAddress': 'OtherAddress',
        'MailingStreet': 'MailingStreet',
        'MailingCity': 'MailingCity',
        'MailingState': 'MailingState',
        'MailingPostalCode': 'MailingPostalCode',
        'MailingCountry': 'MailingCountry',
        'MailingLatitude': 'MailingLatitude',
        'MailingLongitude': 'MailingLongitude',
        'MailingGeocodeAccuracy': 'MailingGeocodeAccuracy',
        'MailingAddress': 'MailingAddress',
        'Fax': 'Fax',
        'MobilePhone': 'MobilePhone',
        'HomePhone': 'HomePhone',
        'OtherPhone': 'OtherPhone',
        'AssistantPhone': 'AssistantPhone',
        'ReportsToId': 'ReportsToId',
        'Title': 'Title',
        'Department': 'Department',
        'AssistantName': 'AssistantName',
        'LeadSource': 'LeadSource',
        'Birthdate': 'Birthdate',
        'Description': 'Description',
        'HasOptedOutOfEmail': 'HasOptedOutOfEmail',
        'HasOptedOutOfFax': 'HasOptedOutOfFax',
        'DoNotCall': 'DoNotCall',
        'LastCURequestDate': 'LastCURequestDate',
        'LastCUUpdateDate': 'LastCUUpdateDate',
        'EmailBouncedReason': 'EmailBouncedReason',
        'EmailBouncedDate': 'EmailBouncedDate',
        'IsEmailBounced': 'IsEmailBounced',
        'IndividualId': 'IndividualId',
        'IsPriorityRecord': 'IsPriorityRecord',
    }

    if bbf_api in exact_matches:
        es_api = exact_matches[bbf_api]
        if es_api:
            for es_field in es_fields:
                if es_field['Field API Name'] == es_api:
                    same_type = (bbf_type == es_field['Field Type'])
                    return (
                        es_field,
                        'High',
                        f"Exact API name match: standard Salesforce Contact field",
                        not same_type
                    )
        else:
            return (None, 'None', f"BBF-specific field: {bbf_label} not present in ES Contact", False)

    # SEMANTIC DOMAIN KNOWLEDGE MATCHING

    # Contact Type multipicklist - ES and BBF both have this with different values
    if bbf_api == 'Contact_Type__c':
        for es_field in es_fields:
            if es_field['Field API Name'] == 'Contact_Type__c':
                return (
                    es_field,
                    'High',
                    "Contact Type multipicklist - both orgs have this field. ES values: Payable, Unknown, Billing, Decision Maker, Maintenance, On-Site, Order, Portal User, Repair. BBF values: Alternate Local Contact, Badge Admin, Billing, Consultant, Engineering, Executive, Hands & Feet, Local Contact, Main, Maintenance, Prospect, Provisioning, Service Order, Site Manager, Technical, Technician, Testing. Some overlap (Billing, Maintenance), needs value translation.",
                    True
                )

    # Mobile Opt Out - BBF has et4ae5__HasOptedOutOfMobile__c, ES might have equivalent
    if bbf_api == 'et4ae5__HasOptedOutOfMobile__c':
        return (None, 'None', 'BBF Marketing Cloud mobile opt-out field - no ES equivalent', False)

    # Mobile Country Code - BBF has et4ae5__Mobile_Country_Code__c for international phone formatting
    if bbf_api == 'et4ae5__Mobile_Country_Code__c':
        return (None, 'None', 'BBF Marketing Cloud mobile country code - no ES equivalent', False)

    # Primary Quote Contact - BBF Proposal Manager package field
    if bbf_api == 'proposalmanager__Primary_Quote_Contact__c':
        return (None, 'None', 'BBF Proposal Manager package field - no ES equivalent', False)

    # Contact validation checkboxes - BBF has formula fields for checking main/maintenance/service/engineering contacts
    if bbf_api.startswith('check') and bbf_api.endswith('Contact__c'):
        return (None, 'None', f'BBF formula field for Contact Type validation - {bbf_label}', False)

    # Marketing preferences - Data center vs Network
    if bbf_api == 'mktg_Network_Preference__c':
        return (None, 'None', 'BBF marketing preference for network services - no direct ES equivalent', False)

    if bbf_api == 'mktg_Data_Center_Preference__c':
        return (None, 'None', 'BBF marketing preference for data center services - no direct ES equivalent', False)

    # Match Key / Unified Contact ID - BBF deduplication fields
    if bbf_api in ('Match_Key__c', 'unifiedContactId__c', 'pin__c'):
        return (None, 'None', f'BBF contact matching/deduplication field: {bbf_label}', False)

    # Test fields
    if bbf_api.startswith('rh2__') and 'Test' in bbf_api:
        return (None, 'None', f'BBF test field: {bbf_label}', False)

    # Formula fields
    if bbf_api == 'Full_Address__c':
        return (None, 'None', 'BBF formula field concatenating address components', False)

    if bbf_api == 'Industry_Vertical__c':
        return (None, 'None', 'BBF formula field derived from Account industry classification', False)

    if bbf_api == 'Verified_Account__c':
        return (None, 'None', 'BBF formula field indicating account verification status', False)

    # Lead Score - BBF has single field, ES has multiple scoring fields
    if bbf_api == 'Lead_Score__c':
        # Check for ES lead scoring fields
        for es_field in es_fields:
            if es_field['Field API Name'] == 'leadScoring__Lead_Score__c':
                return (
                    es_field,
                    'High',
                    'Lead scoring field - ES uses LeadScoring package with Lead_Score__c field',
                    False
                )
        return (None, 'Medium', 'BBF Lead Score - ES has leadScoring__Lead_Score__c, leadScoring__Campaign_Score__c, and leadScoring__Total_Lead_Score__c', False)

    # Direct Phone - BBF custom phone field for direct dial
    if bbf_api == 'Direct_Phone__c':
        # ES might have Phone (already excluded), MobilePhone, or other phone fields
        return (None, 'Low', 'BBF Direct Phone - could map from ES Phone (Day 1 field) or need new data', False)

    # Contact Status - BBF picklist for contact lifecycle status
    if bbf_api == 'Contact_Status__c':
        # ES doesn't appear to have a contact status field
        return (None, 'None', 'BBF Contact Status picklist (Active, Inactive, No Longer There, Invalid Info, Do Not Contact) - no ES equivalent', False)

    # NO MATCH - BBF field has no semantic equivalent in ES
    return (None, 'None', f'No semantic match found for {bbf_label}', False)


def match_picklist_value(es_value: str, bbf_values: List[str]) -> Tuple[str, str]:
    """
    Match an ES picklist value to BBF values using semantic understanding.
    Returns: (suggested_mapping, notes)
    """
    es_lower = es_value.lower().strip()

    # Exact match (case-insensitive)
    for bbf_val in bbf_values:
        if bbf_val.lower().strip() == es_lower:
            return (bbf_val, 'Exact Match')

    # Close semantic matches for common contact domain values
    close_matches = {
        # LeadSource mappings
        'agent': 'Agent',
        'costar': None,  # ES-specific
        'directly engaged': 'Direct Contact',
        'inbound phone call': 'Inbound Web',
        'network map leads': None,  # ES-specific
        'neustar': None,  # ES-specific
        'sales intern lead source': 'Employee Referral',
        'tidio - website chatbot': 'Website',
        'unsolicited prospecting': 'Direct Contact',
        'vendor referral program': 'Vendor',
        'zoominfo': 'ZoomInfo',

        # Contact Type mappings (some overlap)
        'payable': None,  # No BBF equivalent
        'unknown': 'Prospect',  # Closest semantic match
        'billing': 'Billing',  # Exact match
        'decision maker': 'Executive',  # Close match
        'maintenance': 'Maintenance',  # Exact match
        'on-site': 'Hands & Feet',  # Close match
        'order': 'Service Order',  # Close match
        'portal user': 'Main',  # BBF Main contact is primary portal contact
        'repair': 'Technician',  # Close match
    }

    if es_lower in close_matches:
        bbf_match = close_matches[es_lower]
        if bbf_match:
            return (bbf_match, 'Close Match')

    # No match - return all valid BBF values
    all_values = ' | '.join(bbf_values)
    return (all_values, 'No Match - Select from list')


def main():
    print("Loading ES Contact fields...")
    es_fields = load_fields('day-two/exports/es_Contact_fields_with_picklists.csv')
    print(f"  Loaded {len(es_fields)} ES Contact fields")

    print("Loading BBF Contact fields...")
    bbf_fields = load_fields('day-two/exports/bbf_Contact_fields_with_picklists.csv')
    print(f"  Loaded {len(bbf_fields)} BBF Contact fields")

    print("Loading ES picklist values...")
    es_picklists = load_picklist_values('day-two/exports/es_Contact_picklist_values.csv')
    print(f"  Loaded picklist values for {len(es_picklists)} ES fields")

    print("Loading BBF picklist values...")
    bbf_picklists = load_picklist_values('day-two/exports/bbf_Contact_picklist_values.csv')
    print(f"  Loaded picklist values for {len(bbf_picklists)} BBF fields")

    # Filter out excluded fields from BBF
    print("\nFiltering out Day 1 and system fields...")
    excluded = DAY_1_FIELDS | SYSTEM_FIELDS
    bbf_filtered = [f for f in bbf_fields if f['Field API Name'] not in excluded]
    print(f"  {len(bbf_fields)} total BBF fields")
    print(f"  {len(excluded)} excluded fields (Day 1 + system)")
    print(f"  {len(bbf_filtered)} BBF fields to map")

    # Perform semantic matching
    print("\nPerforming AI-powered semantic field matching...")
    field_mappings = []

    for bbf_field in bbf_filtered:
        matched_es, confidence, notes, needs_transformer = semantic_match_contact_field(bbf_field, es_fields)

        mapping = {
            'bbf_field_api': bbf_field['Field API Name'],
            'bbf_label': bbf_field['Field Label'],
            'bbf_type': bbf_field['Field Type'],
            'bbf_required': 'Yes' if bbf_field['Is Nillable'] == 'False' else 'No',
            'es_field_api': matched_es['Field API Name'] if matched_es else '',
            'es_label': matched_es['Field Label'] if matched_es else '',
            'es_type': matched_es['Field Type'] if matched_es else '',
            'confidence': confidence,
            'transformer_needed': 'Y' if needs_transformer else 'N',
            'notes': notes
        }
        field_mappings.append(mapping)

    # Perform picklist value matching
    print("Performing picklist value matching...")
    picklist_mappings = []

    for bbf_field in bbf_filtered:
        bbf_api = bbf_field['Field API Name']
        bbf_type = bbf_field['Field Type']

        # Only process picklist fields that have a match
        if bbf_type not in ('picklist', 'multipicklist'):
            continue

        if bbf_api not in bbf_picklists:
            continue

        # Find the matched ES field
        matched_es_api = None
        for mapping in field_mappings:
            if mapping['bbf_field_api'] == bbf_api and mapping['es_field_api']:
                matched_es_api = mapping['es_field_api']
                break

        if not matched_es_api or matched_es_api not in es_picklists:
            continue

        # Match each ES value to BBF values
        es_values = es_picklists[matched_es_api]
        bbf_values = bbf_picklists[bbf_api]

        for es_value in es_values:
            suggested, match_notes = match_picklist_value(es_value, bbf_values)

            picklist_mappings.append({
                'es_field': matched_es_api,
                'es_value': es_value,
                'bbf_field': bbf_api,
                'suggested_mapping': suggested,
                'notes': match_notes,
                'bbf_final_value': ''
            })

    # Create JSON output
    output_data = {
        'field_mappings': field_mappings,
        'picklist_mappings': picklist_mappings
    }

    json_path = 'day-two/exports/contact_mapping.json'
    print(f"\nWriting mapping data to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    # Print statistics
    high_conf = sum(1 for m in field_mappings if m['confidence'] == 'High')
    medium_conf = sum(1 for m in field_mappings if m['confidence'] == 'Medium')
    low_conf = sum(1 for m in field_mappings if m['confidence'] == 'Low')
    none_conf = sum(1 for m in field_mappings if m['confidence'] == 'None')
    transformers = sum(1 for m in field_mappings if m['transformer_needed'] == 'Y')

    print(f"\nField Mapping Statistics:")
    print(f"  Total BBF Fields: {len(field_mappings)}")
    print(f"  High Confidence: {high_conf}")
    print(f"  Medium Confidence: {medium_conf}")
    print(f"  Low Confidence: {low_conf}")
    print(f"  No Match: {none_conf}")
    print(f"  Transformers Needed: {transformers}")

    if picklist_mappings:
        exact = sum(1 for m in picklist_mappings if m['notes'] == 'Exact Match')
        close = sum(1 for m in picklist_mappings if m['notes'] == 'Close Match')
        no_match = sum(1 for m in picklist_mappings if 'No Match' in m['notes'])

        print(f"\nPicklist Mapping Statistics:")
        print(f"  Total Values: {len(picklist_mappings)}")
        print(f"  Exact Match: {exact}")
        print(f"  Close Match: {close}")
        print(f"  No Match: {no_match}")

    print(f"\nJSON mapping data written to: {json_path}")
    print("Ready to create Excel file using create_mapping_excel.py")


if __name__ == '__main__':
    main()

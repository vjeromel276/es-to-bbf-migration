"""
Create Field Mapping for ES Address__c to BBF Location__c
Uses semantic understanding to match fields by meaning
"""

import pandas as pd
import json
import os
import sys

# Define system fields to exclude
SYSTEM_FIELDS = {
    'Id', 'IsDeleted', 'MasterRecordId', 'CreatedDate', 'CreatedById',
    'LastModifiedDate', 'LastModifiedById', 'SystemModstamp', 'LastActivityDate',
    'LastViewedDate', 'LastReferencedDate', 'JigsawContactId', 'Jigsaw',
    'PhotoUrl', 'CleanStatus', 'RecordTypeId'
}

# Day 1 fields already migrated for Location__c
DAY1_MIGRATED_FIELDS = {
    'Name', 'OwnerId', 'ES_Legacy_ID__c', 'BBF_New_Id__c',
    'Address_Line_1__c', 'Address_Line_2__c', 'City__c',
    'State_Province__c', 'Postal_Code__c', 'Country__c'
}


def load_field_data(es_csv, bbf_csv):
    """Load and filter field metadata from CSV files"""
    es_fields = pd.read_csv(es_csv)
    bbf_fields = pd.read_csv(bbf_csv)

    # Filter out system and Day 1 fields
    bbf_fields = bbf_fields[~bbf_fields['Field API Name'].isin(SYSTEM_FIELDS)]
    bbf_fields = bbf_fields[~bbf_fields['Field API Name'].isin(DAY1_MIGRATED_FIELDS)]

    es_fields = es_fields[~es_fields['Field API Name'].isin(SYSTEM_FIELDS)]

    return es_fields, bbf_fields


def load_picklist_data(es_csv, bbf_csv):
    """Load picklist values"""
    es_picklists = pd.read_csv(es_csv)
    bbf_picklists = pd.read_csv(bbf_csv)
    return es_picklists, bbf_picklists


def semantic_match_fields(bbf_field_api, bbf_field_label, es_fields):
    """
    Use semantic understanding to match BBF field to ES field
    Returns: (es_api_name, es_label, es_type, confidence, transformer_needed, notes)
    """

    # Normalize for comparison
    bbf_api_lower = bbf_field_api.lower()
    bbf_label_lower = bbf_field_label.lower()

    # Special case mappings based on telecom domain knowledge
    semantic_mappings = {
        # CLLI Code mappings - telecom location identifiers
        'cllicode__c': ('CLLI__c', 'High', 'N', 'Exact semantic match - CLLI code is standard telecom location identifier'),
        'legacy_clli_code__c': ('CLLI__c', 'Medium', 'N', 'Could populate from CLLI__c for legacy tracking purposes'),
        'cllicode_last_part__c': (None, 'None', 'Y', 'ES does not have CLLI code component breakdown - would need to parse CLLI__c'),
        'cllicode_old__c': (None, 'None', 'N', 'No equivalent old CLLI tracking in ES Address__c'),

        # Address validation fields
        'address_api_status__c': (None, 'Low', 'Y', 'ES has Verified__c (boolean) and Address_Return_Code__c - needs transformation to picklist status'),
        'address_validated_by__c': ('Verification_Used__c', 'High', 'Y', 'Maps to Verification_Used__c - picklist values partially overlap (SmartyStreets, Google)'),
        'address_api_message__c': ('Address_Return_Code__c', 'Medium', 'N', 'ES Address_Return_Code__c stores validation API response codes'),

        # Business Unit / Market segmentation
        'businessunit__c': ('Dimension_4_Market__c', 'Medium', 'Y', 'ES uses Dimension_4_Market__c for market segmentation - BBF uses business unit model, requires value mapping'),
        'business_unit__c': ('Dimension_4_Market__c', 'Medium', 'Y', 'Text field - populate from Dimension_4_Market__c with transformation'),
        'region__c': (None, 'None', 'Y', 'ES does not have region concept - would need geographic calculation from State__c'),

        # Wire Center and Ring - telecom network hierarchy
        'wire_center__c': (None, 'None', 'N', 'ES does not have wire center lookup - BBF specific concept'),
        'ring__c': (None, 'None', 'N', 'ES does not have ring/network ring concept - BBF specific'),
        'market_mapping_name__c': ('Dimension_4_Market__c', 'Low', 'Y', 'Could potentially derive from Dimension_4_Market__c'),
        'market__c': ('Dimension_4_Market__c', 'Medium', 'Y', 'Text field - map from Dimension_4_Market__c picklist values'),

        # Geographic identifiers
        'cvaddressid__c': (None, 'None', 'N', 'ES does not use CableVision address IDs - BBF legacy system'),
        'unifiedaddressid__c': (None, 'None', 'N', 'ES does not have unified address ID concept'),
        'unique_key__c': ('Unique_Constraint_Check__c', 'Medium', 'Y', 'ES uses Unique_Constraint_Check__c for address deduplication - similar purpose'),
        'match_key__c': ('Unique_Constraint_Check__c', 'Medium', 'Y', 'Similar purpose - unique address matching key'),
        'full_address__c': ('Output_Document_Address__c', 'High', 'Y', 'ES has formula field Output_Document_Address__c for formatted address'),
        'common_name__c': ('Organization__c', 'Medium', 'N', 'ES Organization__c tracks building/location name'),

        # Street address components - different parsing approaches
        'street__c': ('Address__c', 'High', 'N', 'ES Address__c contains full street address'),
        'streetno__c': (None, 'Low', 'Y', 'ES stores full address in Address__c - would need parsing for street number'),
        'strname__c': ('Thoroughfare_Name__c', 'Medium', 'N', 'ES has Thoroughfare_Name__c from geocoding service'),
        'strsuffix__c': (None, 'Low', 'Y', 'ES stores complete address - would need parsing for street suffix'),
        'strdir__c': (None, 'Low', 'Y', 'ES does not break out street direction separately - in Address__c'),

        # Geolocation coordinates
        'loc__c': ('Geocode_Lat_Long__c', 'High', 'N', 'Direct mapping - both are geolocation (lat/long) fields'),

        # State/Province handling
        'statecode__c': ('State__c', 'High', 'N', 'ES State__c is picklist with 2-letter abbreviations'),
        'state__c': ('State__c', 'High', 'Y', 'ES State__c stores abbreviations - may need expansion to full state name'),

        # Postal code
        'postalcode__c': ('Zip__c', 'High', 'N', 'ES uses Zip__c field for postal/zip codes'),

        # ROE (Right of Entry) fields - customer access management
        'roe_contact_name__c': (None, 'None', 'N', 'ES does not track Right of Entry contact information'),
        'roe_email__c': (None, 'None', 'N', 'ES does not track ROE contact email'),
        'roe_phone_number__c': (None, 'None', 'N', 'ES does not track ROE contact phone'),
        'roe_position__c': (None, 'None', 'N', 'ES does not track ROE contact position/title'),
        'roe_type__c': (None, 'None', 'N', 'ES does not track ROE type (Tenant/Landlord)'),
        'roe_contact_name_lookup__c': (None, 'None', 'N', 'ES does not have ROE contact lookup relationship'),

        # Service appointment tracking
        'service_appointment_count__c': (None, 'None', 'N', 'ES does not track service appointments on Address object'),
        'a_location_service__c': (None, 'None', 'N', 'ES does not have A-location service counts'),
        'z_location_service__c': (None, 'None', 'N', 'ES does not have Z-location service counts'),

        # Control flags
        'name_is_set_manually__c': (None, 'None', 'N', 'ES does not have this control flag for manual naming'),

        # Legacy identifiers
        'old_siteid__c': ('Site_ID__c', 'High', 'N', 'ES has Site_ID__c field for legacy site tracking'),

        # County
        'county__c': ('County__c', 'High', 'N', 'Exact match - both track county/parish'),

        # Formula field for street display
        'location_street__c': ('Output_Document_Address__c', 'Medium', 'Y', 'BBF formula field - ES equivalent is Output_Document_Address__c'),
    }

    # Check if we have a predefined semantic mapping
    if bbf_api_lower in semantic_mappings:
        es_field, confidence, transformer, notes = semantic_mappings[bbf_api_lower]
        if es_field:
            es_row = es_fields[es_fields['Field API Name'] == es_field]
            if not es_row.empty:
                return (es_field, es_row.iloc[0]['Field Label'], es_row.iloc[0]['Field Type'],
                        confidence, transformer, notes)
        return (None, None, None, confidence, transformer, notes)

    # Try exact API name match
    for _, es_row in es_fields.iterrows():
        if es_row['Field API Name'].lower() == bbf_api_lower:
            return (es_row['Field API Name'], es_row['Field Label'], es_row['Field Type'],
                    'High', 'N', 'Exact API name match')

    # Try label match
    for _, es_row in es_fields.iterrows():
        if es_row['Field Label'].lower() == bbf_label_lower:
            return (es_row['Field API Name'], es_row['Field Label'], es_row['Field Type'],
                    'Medium', 'N', 'Label match')

    # No match found
    return (None, None, None, 'None', 'N', 'No equivalent field found in ES Address__c')


def create_field_mappings(bbf_fields, es_fields):
    """Create field mapping array"""
    mappings = []

    for _, bbf_row in bbf_fields.iterrows():
        bbf_api = bbf_row['Field API Name']
        bbf_label = bbf_row['Field Label']
        bbf_type = bbf_row['Field Type']
        bbf_required = 'No' if bbf_row['Is Nillable'] else 'Yes'

        # Get semantic match
        es_api, es_label, es_type, confidence, transformer, notes = semantic_match_fields(
            bbf_api, bbf_label, es_fields
        )

        mappings.append({
            'bbf_field_api': bbf_api,
            'bbf_label': bbf_label,
            'bbf_type': bbf_type,
            'bbf_required': bbf_required,
            'es_field_api': es_api if es_api else '',
            'es_label': es_label if es_label else '',
            'es_type': es_type if es_type else '',
            'confidence': confidence,
            'transformer_needed': transformer,
            'notes': notes
        })

    return mappings


def create_picklist_mappings(es_picklists, bbf_picklists, field_mappings):
    """Create picklist value mappings with left-to-right workflow"""
    picklist_mappings = []

    # Get all picklist field mappings
    for fm in field_mappings:
        if fm['es_field_api'] and fm['bbf_type'] == 'picklist':
            es_field = fm['es_field_api']
            bbf_field = fm['bbf_field_api']

            # Get ES picklist values
            es_values = es_picklists[es_picklists['Field API Name'] == es_field]
            # Get BBF picklist values
            bbf_values = bbf_picklists[bbf_picklists['Field API Name'] == bbf_field]
            bbf_value_list = bbf_values['Picklist Value'].tolist()

            if es_values.empty:
                continue

            for _, es_val_row in es_values.iterrows():
                es_value = es_val_row['Picklist Value']

                # Try exact match
                exact_match = bbf_values[bbf_values['Picklist Value'] == es_value]
                if not exact_match.empty:
                    picklist_mappings.append({
                        'es_field': es_field,
                        'es_value': es_value,
                        'bbf_field': bbf_field,
                        'suggested_mapping': es_value,
                        'notes': 'Exact Match',
                        'bbf_final_value': ''
                    })
                    continue

                # Try case-insensitive match
                es_lower = es_value.lower()
                close_match = None
                for bbf_val in bbf_value_list:
                    if bbf_val.lower() == es_lower:
                        close_match = bbf_val
                        break

                if close_match:
                    picklist_mappings.append({
                        'es_field': es_field,
                        'es_value': es_value,
                        'bbf_field': bbf_field,
                        'suggested_mapping': close_match,
                        'notes': 'Close Match',
                        'bbf_final_value': ''
                    })
                    continue

                # Semantic matching for specific field pairs
                suggested = None
                match_note = 'No Match - Select from list'

                # Address_Validated_By__c mapping
                if bbf_field == 'Address_Validated_By__c' and es_field == 'Verification_Used__c':
                    if es_value == 'SmartyStreets':
                        suggested = 'SmartyStreets'
                        match_note = 'Exact Match'
                    elif es_value == 'Google Maps':
                        suggested = 'Google'
                        match_note = 'Close Match - Google Maps → Google'
                    elif es_value == 'UPS':
                        # No equivalent in BBF
                        suggested = ' | '.join(bbf_value_list)
                        match_note = 'No Match - Select from list'

                # If we have a specific suggestion
                if suggested and ' | ' not in suggested:
                    picklist_mappings.append({
                        'es_field': es_field,
                        'es_value': es_value,
                        'bbf_field': bbf_field,
                        'suggested_mapping': suggested,
                        'notes': match_note,
                        'bbf_final_value': ''
                    })
                else:
                    # No match - list all BBF values
                    all_values = ' | '.join(bbf_value_list)
                    picklist_mappings.append({
                        'es_field': es_field,
                        'es_value': es_value,
                        'bbf_field': bbf_field,
                        'suggested_mapping': all_values if not suggested else suggested,
                        'notes': match_note,
                        'bbf_final_value': ''
                    })

    return picklist_mappings


def main():
    # Define paths
    base_dir = '/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration'
    es_fields_csv = os.path.join(base_dir, 'day-two/exports/es_Address__c_fields_with_picklists.csv')
    bbf_fields_csv = os.path.join(base_dir, 'day-two/exports/bbf_Location__c_fields_with_picklists.csv')
    es_picklists_csv = os.path.join(base_dir, 'day-two/exports/es_Address__c_picklist_values.csv')
    bbf_picklists_csv = os.path.join(base_dir, 'day-two/exports/bbf_Location__c_picklist_values.csv')
    json_output = os.path.join(base_dir, 'day-two/exports/address_location_mapping.json')
    excel_output = os.path.join(base_dir, 'day-two/mappings/ES_Address__c_to_BBF_Location__c_mapping.xlsx')

    print("Loading field metadata...")
    es_fields, bbf_fields = load_field_data(es_fields_csv, bbf_fields_csv)
    es_picklists, bbf_picklists = load_picklist_data(es_picklists_csv, bbf_picklists_csv)

    print(f"ES Address__c fields (after filtering): {len(es_fields)}")
    print(f"BBF Location__c fields (after filtering): {len(bbf_fields)}")

    print("\nCreating semantic field mappings...")
    field_mappings = create_field_mappings(bbf_fields, es_fields)

    print("Creating picklist value mappings...")
    picklist_mappings = create_picklist_mappings(es_picklists, bbf_picklists, field_mappings)

    # Create JSON output
    mapping_data = {
        'field_mappings': field_mappings,
        'picklist_mappings': picklist_mappings
    }

    print(f"\nSaving JSON to {json_output}...")
    with open(json_output, 'w') as f:
        json.dump(mapping_data, f, indent=2)

    # Print summary
    high_conf = sum(1 for m in field_mappings if m['confidence'] == 'High')
    medium_conf = sum(1 for m in field_mappings if m['confidence'] == 'Medium')
    low_conf = sum(1 for m in field_mappings if m['confidence'] == 'Low')
    none_conf = sum(1 for m in field_mappings if m['confidence'] == 'None')
    transformers = sum(1 for m in field_mappings if m['transformer_needed'] == 'Y')

    print(f"\nField Mapping Summary:")
    print(f"  BBF Fields: {len(bbf_fields)}")
    print(f"  ES Fields: {len(es_fields)}")
    print(f"  High Confidence Matches: {high_conf}")
    print(f"  Medium Confidence Matches: {medium_conf}")
    print(f"  Low/No Match (Need Review): {low_conf + none_conf}")
    print(f"  Transformers Needed: {transformers}")

    if picklist_mappings:
        exact = sum(1 for m in picklist_mappings if m['notes'] == 'Exact Match')
        close = sum(1 for m in picklist_mappings if 'Close Match' in m['notes'])
        no_match = sum(1 for m in picklist_mappings if 'No Match' in m['notes'])
        print(f"\nPicklist Mapping Summary:")
        print(f"  Picklist Fields Mapped: {len(set(m['bbf_field'] for m in picklist_mappings))}")
        print(f"  Total Value Mappings: {len(picklist_mappings)}")
        print(f"    Exact Match: {exact}")
        print(f"    Close Match: {close}")
        print(f"    No Match: {no_match}")

    print(f"\nJSON mapping data saved to: {json_output}")
    print(f"\nNext step: Run create_mapping_excel.py to generate Excel workbook")
    print(f"  python day-two/tools/create_mapping_excel.py --mapping-json {json_output} --output {excel_output}")


if __name__ == '__main__':
    main()

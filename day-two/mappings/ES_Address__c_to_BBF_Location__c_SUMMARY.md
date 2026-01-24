# Address__c (ES) to Location__c (BBF) Field Mapping Summary

**Generated**: 2026-01-15
**Mapping File**: `ES_Address__c_to_BBF_Location__c_mapping.xlsx`

## Overview

This document summarizes the field mapping analysis between ES Address__c (source) and BBF Location__c (target) objects for Day Two enrichment.

## Statistics

### Field Mapping (Sheet 1)
- **Total BBF Fields**: 56 (43 after exclusions)
- **Total ES Fields**: 122
- **Excluded System Fields**: 11 (Id, IsDeleted, CreatedDate, etc.)
- **Excluded Day 1 Fields**: 10 (Name, OwnerId, ES_Legacy_ID__c, etc.)

### Match Quality
- **High Confidence**: 3 fields (exact API name or normalized match)
- **Medium Confidence**: 19 fields (label match or semantic match)
- **Low Confidence**: 4 fields (weak semantic match)
- **No Match**: 17 fields (no ES source identified)

### Transformation Requirements
- **Transformers Needed**: 13 fields (type mismatch, length difference, or picklist translation)

### Picklist Mapping (Sheet 2)
- **BBF Picklist Fields**: 5 fields
- **Total Picklist Values Mapped**: 20 values
- **Format**: Left-to-right workflow (ES source → BBF target → Suggested Mapping → Notes → User Decision)

## Key Findings

### Strong Matches (High Confidence)
1. **RecordTypeId** → **RecordTypeId** (exact API name match)
2. **CLLICode__c** → **CLLI__c** (CLLI code mapping)
3. *(Only 3 high confidence matches found)*

### Good Matches (Medium Confidence)
- **City__c** → **City__c** (semantic match)
- **PostalCode__c** → **Zip__c** (postal code to zip)
- **County__c** → **County__c** (semantic match)
- **StateCode__c** → **State__c** (state code mapping - needs transformer)

### Unmapped Fields (No Match - 17 fields)
These BBF fields have no obvious ES source:
- Common_Name__c
- Loc__c (Geolocation)
- UnifiedAddressId__c
- Unique_Key__c
- Wire_Center__c
- Business_Unit__c
- Match_Key__c
- ROE_Contact_Name__c
- ROE_Email__c
- ROE_Phone_Number__c
- ROE_Position__c
- ROE_Type__c
- ROE_Contact_Name_Lookup__c
- Region__c
- Ring__c
- Market_Mapping_Name__c
- Market__c

### Street Address Parsing Challenge
BBF has granular street address fields, but ES combines them:
- **BBF Fields**: Street__c, strName__c, strDir__c, strSuffix__c, streetNo__c
- **ES Field**: Address__c (combined full address)
- **Action Required**: Need address parsing transformer to split ES Address__c into BBF components

## Picklist Mappings

### Fields Without ES Picklist Source
The following BBF picklist fields have no matching ES picklist source:
1. **Address_API_Status__c**: Values = Validation Is Required | Pending | Valid | Not Valid | Error
2. **Address_Validated_By__c**: Values = SmartyStreets | Google | Manually
3. **businessUnit__c**: Values = BBU | INA | MNA | UFMW | BBQC | MTI | EVS
4. **ROE_Type__c**: Values = Tenant | Landlord
5. **Region__c**: Values = Central | North | West

**Note**: ES has picklist fields (State__c, Verification_Used__c, Building_Status__c, etc.) but they don't map to BBF Location__c picklists.

## Recommendations

### Immediate Actions
1. **Review Unmapped Fields**: Determine if these 17 BBF fields need data sources or can remain blank for migration
2. **Address Parsing**: Develop transformer to parse ES Address__c into BBF street components
3. **Business Unit Mapping**: Get business decision on how to populate businessUnit__c (BBU, INA, MNA, etc.)
4. **Region Mapping**: Get business decision on how to populate Region__c (Central, North, West)

### Data Quality Concerns
1. **Geolocation (Loc__c)**: ES has Geocode_Lat_Long__c but needs verification if this should map
2. **CLLI Code**: ES has CLLI__c (string, 200 chars), BBF has CLLICode__c (string, 11 chars) - needs length validation/truncation
3. **State Codes**: BBF StateCode__c vs State__c - clarify which to use and how they differ

### Transformer Requirements
These 13 fields need transformers due to:
- **Type Mismatch**: CLLICode_Last_Part__c (ES=string, BBF=double)
- **Length Mismatch**: Several fields where ES field is longer than BBF
- **Picklist Translation**: StateCode__c requires picklist value translation
- **Address Parsing**: Street components need parsing from combined Address field

## Excel Workbook Structure

### Sheet 1: Field_Mapping
Columns:
1. BBF_Field_API_Name
2. BBF_Field_Label
3. BBF_Data_Type
4. BBF_Is_Required
5. ES_Field_API_Name
6. ES_Field_Label
7. ES_Data_Type
8. Match_Confidence (color-coded: Green=High, Yellow=Medium, Red=Low/None)
9. Transformer_Needed (Y/N)
10. Notes

### Sheet 2: Picklist_Mapping
Columns (left-to-right workflow):
1. **ES_Field** (source field)
2. **ES_Picklist_Value** (source value)
3. **BBF_Field** (target field)
4. **Suggested_Mapping** (exact match OR complete list of valid BBF values separated by " | ")
5. **Notes** (Exact Match / Close Match / No Match - Select from list)
6. **BBF_Final_Value** (EMPTY - for user decision)

**Note**: The Suggested_Mapping column shows ALL valid BBF values when no exact match exists (no "..." truncation).

## Next Steps

1. **Business Review**: Share this mapping with business stakeholders for review
2. **Field Priority**: Get business to prioritize which unmapped fields are critical for Day Two
3. **Transformer Development**: Begin building transformers for the 13 identified fields
4. **Address Parser**: Develop and test address parsing logic for street components
5. **Picklist Decisions**: Get business mapping decisions for the 5 unmapped picklist fields

## Files Generated

- **Mapping Excel**: `day-two/mappings/ES_Address__c_to_BBF_Location__c_mapping.xlsx`
- **ES Exports**: `day-two/exports/es_Address__c_fields_with_picklists.csv`
- **ES Picklists**: `day-two/exports/es_Address__c_picklist_values.csv`
- **BBF Exports**: `day-two/exports/bbf_Location__c_fields_with_picklists.csv`
- **BBF Picklists**: `day-two/exports/bbf_Location__c_picklist_values.csv`
- **Summary**: `day-two/mappings/ES_Address__c_to_BBF_Location__c_SUMMARY.md` (this file)

---
*Generated by Day Two Field Mapping Agent - 2026-01-15*

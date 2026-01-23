# Field Mapping Summary: Address__c -> Location__c

Generated: 2026-01-21 14:17:48
Source: `ES_Address__c_to_BBF_Location__c_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 42 |
| Fields with ES Match | 20 |
| Fields without ES Match | 22 |
| Transformers Needed | 16 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 10 | 23% |
| Medium | 10 | 23% |
| Low | 5 | 11% |
| None | 17 | 40% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 10 |
| Include: No | 0 |
| Include: TBD | 32 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 2 |
| Total Values | 20 |
| Exact Match | 1 |
| Close Match | 1 |
| No Match | 18 |

## Action Items

### Fields Needing Transformers (9)

- **Full_Address__c** <- Output_Document_Address__c: string <- string
- **State__c** <- State__c: string <- picklist
- **Unique_Key__c** <- Unique_Constraint_Check__c: string <- string
- **Address_Validated_By__c** <- Verification_Used__c: picklist <- picklist
- **Business_Unit__c** <- Dimension_4_Market__c: string <- picklist
- **Match_Key__c** <- Unique_Constraint_Check__c: string <- string
- **businessUnit__c** <- Dimension_4_Market__c: picklist <- picklist
- **Location_Street__c** <- Output_Document_Address__c: string <- string
- **Market__c** <- Dimension_4_Market__c: string <- picklist

### Fields Pending Decision (32)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (10):**
- Common_Name__c <- Organization__c
- Unique_Key__c <- Unique_Constraint_Check__c
- strName__c <- Thoroughfare_Name__c
- Address_API_Message__c <- Address_Return_Code__c
- Business_Unit__c <- Dimension_4_Market__c
- Match_Key__c <- Unique_Constraint_Check__c
- businessUnit__c <- Dimension_4_Market__c
- Location_Street__c <- Output_Document_Address__c
- Market__c <- Dimension_4_Market__c
- Legacy_CLLI_Code__c <- CLLI__c

**Low/No Confidence (22):**
- CLLICode_Last_Part__c: ES does not have CLLI code component breakdown - would need to parse CLLI__c
- CVAddressId__c: ES does not use CableVision address IDs - BBF legacy system
- UnifiedAddressId__c: ES does not have unified address ID concept
- Wire_Center__c: ES does not have wire center lookup - BBF specific concept
- strDir__c: ES does not break out street direction separately - in Address__c
- strSuffix__c: ES stores complete address - would need parsing for street suffix
- streetNo__c: ES stores full address in Address__c - would need parsing for street number
- Address_API_Status__c: ES has Verified__c (boolean) and Address_Return_Code__c - needs transformation to picklist status
- Service_Appointment_Count__c: ES does not track service appointments on Address object
- Name_Is_Set_Manually__c: ES does not have this control flag for manual naming
- ... and 12 more

### Picklist Values Needing Mapping (18)

**Verification_Used__c:**
- `UPS`

**Dimension_4_Market__c:**
- `Cleveland`
- `Columbus`
- `Detroit`
- `Harrisburg`
- `Illinois`
- ... and 12 more

## High Confidence Mappings (10)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| CLLICode__c | CLLI__c | string |
| Full_Address__c | Output_Document_Address__c | string |
| Loc__c | Geocode_Lat_Long__c | location |
| PostalCode__c | Zip__c | string |
| StateCode__c | State__c | string |
| State__c | State__c | string |
| old_SiteId__c | Site_ID__c | string |
| Address_Validated_By__c | Verification_Used__c | picklist |
| Street__c | Address__c | string |
| County__c | County__c | string |

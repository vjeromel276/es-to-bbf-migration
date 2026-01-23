# Field Mapping Summary: Contact -> Contact

Generated: 2026-01-21 14:17:48
Source: `ES_Contact_to_BBF_Contact_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 66 |
| Fields with ES Match | 44 |
| Fields without ES Match | 22 |
| Transformers Needed | 5 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 43 | 65% |
| Medium | 1 | 1% |
| Low | 0 | 0% |
| None | 22 | 33% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 43 |
| Include: No | 0 |
| Include: TBD | 23 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 5 |
| Total Values | 47 |
| Exact Match | 31 |
| Close Match | 0 |
| No Match | 16 |

## Action Items

### Fields Needing Transformers (5)

- **Salutation** <- Salutation: picklist <- picklist
- **OtherGeocodeAccuracy** <- OtherGeocodeAccuracy: picklist <- picklist
- **MailingGeocodeAccuracy** <- MailingGeocodeAccuracy: picklist <- picklist
- **LeadSource** <- LeadSource: picklist <- picklist
- **Contact_Type__c** <- Contact_Type__c: multipicklist <- multipicklist

### Fields Pending Decision (23)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (1):**
- et4ae5__HasOptedOutOfMobile__c <- HasOptedOutOfEmail

**Low/No Confidence (22):**
- MiddleName: No obvious ES source field found - may need business rules or default value
- Suffix: No obvious ES source field found - may need business rules or default value
- proposalmanager__Primary_Quote_Contact__c: No obvious ES source field found - may need business rules or default value
- et4ae5__Mobile_Country_Code__c: No obvious ES source field found - may need business rules or default value
- checkEngineeringContact__c: No obvious ES source field found - may need business rules or default value
- checkMainContact__c: No obvious ES source field found - may need business rules or default value
- checkMaintenanceContact__c: No obvious ES source field found - may need business rules or default value
- checkServiceContact__c: No obvious ES source field found - may need business rules or default value
- mktg_Network_Preference__c: No obvious ES source field found - may need business rules or default value
- mktg_Data_Center_Preference__c: No obvious ES source field found - may need business rules or default value
- ... and 12 more

### Picklist Values Needing Mapping (16)

**LeadSource:**
- `CoStar`
- `Directly Engaged`
- `Inbound Phone Call`
- `Network Map Leads`
- `Neustar`
- ... and 4 more

**Contact_Type__c:**
- `Payable`
- `Unknown`
- `Decision Maker`
- `On-Site`
- `Order`
- ... and 2 more

## High Confidence Mappings (43)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| Salutation | Salutation | picklist |
| OtherStreet | OtherStreet | textarea |
| OtherCity | OtherCity | string |
| OtherState | OtherState | string |
| OtherPostalCode | OtherPostalCode | string |
| OtherCountry | OtherCountry | string |
| OtherLatitude | OtherLatitude | double |
| OtherLongitude | OtherLongitude | double |
| OtherGeocodeAccuracy | OtherGeocodeAccuracy | picklist |
| OtherAddress | OtherAddress | address |
| MailingStreet | MailingStreet | textarea |
| MailingCity | MailingCity | string |
| MailingState | MailingState | string |
| MailingPostalCode | MailingPostalCode | string |
| MailingCountry | MailingCountry | string |
| MailingLatitude | MailingLatitude | double |
| MailingLongitude | MailingLongitude | double |
| MailingGeocodeAccuracy | MailingGeocodeAccuracy | picklist |
| MailingAddress | MailingAddress | address |
| Fax | Fax | phone |
| ... | 23 more | ... |

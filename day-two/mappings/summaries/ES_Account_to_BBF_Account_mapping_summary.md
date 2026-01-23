# Field Mapping Summary: Account -> Account

Generated: 2026-01-21 14:17:48
Source: `ES_Account_to_BBF_Account_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 150 |
| Fields with ES Match | 62 |
| Fields without ES Match | 88 |
| Transformers Needed | 4 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 58 | 38% |
| Medium | 4 | 2% |
| Low | 0 | 0% |
| None | 88 | 58% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 58 |
| Include: No | 0 |
| Include: TBD | 92 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 11 |
| Total Values | 102 |
| Exact Match | 44 |
| Close Match | 22 |
| No Match | 36 |

## Action Items

### Fields Needing Transformers (4)

- **proposalmanager__Primary_State__c** <- Legally_Organized_Under__c: multipicklist <- picklist
- **proposalmanager__Tax_Exempt__c** <- Sales_Tax_Exemption__c: picklist <- boolean
- **Business_Unit__c** <- OneCommunity_Entity__c: string <- picklist
- **Full_Company_Name__c** <- Company_Legal_Name__c: string <- textarea

### Fields Pending Decision (92)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (4):**
- proposalmanager__Primary_State__c <- Legally_Organized_Under__c
- proposalmanager__Tax_Exempt__c <- Sales_Tax_Exemption__c
- Business_Unit__c <- OneCommunity_Entity__c
- Full_Company_Name__c <- Company_Legal_Name__c

**Low/No Confidence (88):**
- RecordTypeId: ES does not use record types for Account
- State_Tax_ID__c: No equivalent ES field for state tax ID
- proposalmanager__CLLI__c: CLLI code - not present in ES
- proposalmanager__Customer_Maintenance_Events_Email__c: Customer maintenance email - ES specific field not present
- proposalmanager__Customer_NOC_Email__c: Customer NOC email - not in ES
- proposalmanager__Customer_NOC_Phone__c: Customer NOC phone - not in ES
- proposalmanager__Quote_Provider_Type__c: Quote provider type - not in ES
- proposalmanager__Quote_Provider__c: Quote provider flag - not in ES
- proposalmanager__Secondary_States__c: Secondary states - not in ES
- proposalmanager__Org_Account_For_PMT_Quotes__c: PMT quotes org account - not in ES
- ... and 78 more

### Picklist Values Needing Mapping (36)

**Type:**
- `Vendor`
- `Other`
- `Customer`
- `Sales Prospect`
- `Vendor`
- ... and 2 more

**Industry:**
- `Accommodation`
- `Administrative`
- `Construction & Engineering`
- `Management`
- `Manufacturing`
- ... and 3 more

**AccountSource:**
- `Neustar`
- `CoStar`
- `Inbound Phone Call`
- `Network Map Leads`
- `Neustar`
- ... and 2 more

**Master_Service_Agreement_MSA__c:**
- `Pending external approval`
- `Pending internal approval`
- `Legal Review`
- `Executed – on File`

**Contract_Type__c:**
- `IRU`

**Legal_Entity_Required_MSA__c:**
- `Municipal Entity (City, County, Township, Village, etc.)`
- `Non-Profit (501c)`
- `General Partnership`

**OneCommunity_Entity__c:**
- `Everstream Ohio`
- `Everstream Michigan`
- `Michigan-LB`
- `OneCommunity`
- `Michigan-RF`
- ... and 1 more

## High Confidence Mappings (58)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| Type | Type | picklist |
| ParentId | ParentId | reference |
| BillingStreet | BillingStreet | textarea |
| BillingCity | BillingCity | string |
| BillingState | BillingState | string |
| BillingPostalCode | BillingPostalCode | string |
| BillingCountry | BillingCountry | string |
| BillingLatitude | BillingLatitude | double |
| BillingLongitude | BillingLongitude | double |
| BillingGeocodeAccuracy | BillingGeocodeAccuracy | picklist |
| BillingAddress | BillingAddress | address |
| ShippingStreet | ShippingStreet | textarea |
| ShippingCity | ShippingCity | string |
| ShippingState | ShippingState | string |
| ShippingPostalCode | ShippingPostalCode | string |
| ShippingCountry | ShippingCountry | string |
| ShippingLatitude | ShippingLatitude | double |
| ShippingLongitude | ShippingLongitude | double |
| ShippingGeocodeAccuracy | ShippingGeocodeAccuracy | picklist |
| ShippingAddress | ShippingAddress | address |
| ... | 38 more | ... |

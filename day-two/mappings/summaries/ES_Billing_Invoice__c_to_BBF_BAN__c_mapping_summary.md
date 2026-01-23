# Field Mapping Summary: Billing_Invoice__c -> BAN__c

Generated: 2026-01-21 14:17:48
Source: `ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 80 |
| Fields with ES Match | 10 |
| Fields without ES Match | 70 |
| Transformers Needed | 3 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 6 | 7% |
| Medium | 4 | 5% |
| Low | 0 | 0% |
| None | 70 | 87% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 6 |
| Include: No | 0 |
| Include: TBD | 74 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 4 |
| Total Values | 7 |
| Exact Match | 2 |
| Close Match | 4 |
| No Match | 1 |

## Action Items

### Fields Needing Transformers (3)

- **Billing_State__c** <- Billing_State__c: string <- picklist
- **invType__c** <- Invoice_Delivery_Preference__c: picklist <- picklist
- **Billing_Schedule_Group__c** <- Invoice_cycle_cd__c: picklist <- picklist

### Fields Pending Decision (74)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (4):**
- invType__c <- Invoice_Delivery_Preference__c
- BAN_Description__c <- Description__c
- Billing_Schedule_Group__c <- Invoice_cycle_cd__c
- General_Description__c <- Billing_Notes__c

**Low/No Confidence (70):**
- Billing_Location__c: BBF-specific field - no ES equivalent. Requires business rule or default value.
- MatchKey__c: BBF-specific field - no ES equivalent. Requires business rule or default value.
- busUnit__c: Business Unit - no ES equivalent. Requires business rule/default (e.g., "EVS" for EverStream accounts).
- Federal_Tax_ID__c: Tax ID field - no ES equivalent. May need to extract from Account or manual entry.
- Industry__c: Industry classification - deprecated field. May copy from Account.Industry if needed.
- State_Tax_ID__c: Tax ID field - no ES equivalent. May need to extract from Account or manual entry.
- Customer_Posting_Group__c: Customer Posting Group - financial/ERP field. Requires business rule or Account classification.
- Contract_Type__c: Contract Type - no ES equivalent. May derive from Account or Order data.
- Vertical__c: BBF-specific field - no ES equivalent. Requires business rule or default value.
- Active_Charges__c: Calculated/rollup field - auto-populated from related Service records.
- ... and 60 more

### Picklist Values Needing Mapping (1)

**Invoice_cycle_cd__c:**
- `Manual`

## High Confidence Mappings (6)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| Billing_City__c | Billing_City__c | string |
| Billing_PostalCode__c | Billing_ZIP__c | string |
| Billing_State__c | Billing_State__c | string |
| Billing_Street__c | Billing_Address_1__c | string |
| Billing_Company_Name__c | Account_Name__c | string |
| Payment_Terms__c | Payment_Terms__c | picklist |

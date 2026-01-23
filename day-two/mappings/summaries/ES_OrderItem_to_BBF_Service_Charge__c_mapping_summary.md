# Field Mapping Summary: OrderItem -> Service_Charge__c

Generated: 2026-01-21 14:17:48
Source: `ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 45 |
| Fields with ES Match | 18 |
| Fields without ES Match | 27 |
| Transformers Needed | 19 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 10 | 22% |
| Medium | 8 | 17% |
| Low | 8 | 17% |
| None | 19 | 42% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 10 |
| Include: No | 0 |
| Include: TBD | 35 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 2 |
| Total Values | 8 |
| Exact Match | 0 |
| Close Match | 1 |
| No Match | 7 |

## Action Items

### Fields Needing Transformers (11)

- **Description__c** <- Description: textarea <- string
- **Sequence__c** <- OrderItemNumber: string <- string
- **Amount__c** <- Total_MRC_Amortized__c: currency <- currency
- **PricebookEntryId__c** <- PricebookEntryId: string <- reference
- **Charge_Class__c** <- SBQQ__ChargeType__c: picklist <- picklist
- **Charge_Active__c** <- SBQQ__Activated__c: boolean <- boolean
- **Bill_Schedule_Type__c** <- SBQQ__BillingFrequency__c: picklist <- picklist
- **MRC_Net__c** <- Total_MRC_Amortized__c: currency <- currency
- **NRC_Net__c** <- NRC_Non_Amortized__c: currency <- currency
- **Active__c** <- SBQQ__Activated__c: boolean <- boolean
- **Off_Net__c** <- OFF_NET_IDs__c: reference <- string

### Fields Pending Decision (35)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (8):**
- Sequence__c <- OrderItemNumber
- Charge_Class__c <- SBQQ__ChargeType__c
- Charge_Active__c <- SBQQ__Activated__c
- Bill_Schedule_Type__c <- SBQQ__BillingFrequency__c
- MRC_Net__c <- Total_MRC_Amortized__c
- NRC_Net__c <- NRC_Non_Amortized__c
- Active__c <- SBQQ__Activated__c
- Off_Net__c <- OFF_NET_IDs__c

**Low/No Confidence (27):**
- Charge__c: Deprecated charge type reference - not used in migration
- Match_Key__c: BBF matching key - generate from OrderItem.Id or unique combination
- Unified_DB_Last_Synced_Date__c: BBF sync timestamp - not applicable for migration
- Product_Category__c: Deprecated product category (formula) - may derive from Product_Family__c
- Product_Name__c: Deprecated product name (formula) - direct match if needed
- Product__c: Deprecated product reference - maps to Product2Id
- Test_Formula__c: Test formula field - not used in migration
- Service_Order_Line_Charge__c: Reference to originating quote line - may map to SBQQ__QuoteLine__c if needed
- SC_Record_Type__c: Service Charge record type (Charge vs COGS) - set based on charge nature
- Disabled_COPS_Synchronization__c: BBF-specific field for COPS sync control - no ES equivalent
- ... and 17 more

### Picklist Values Needing Mapping (7)

**SBQQ__ChargeType__c:**
- `One-Time`
- `Usage`

**SBQQ__BillingFrequency__c:**
- `Monthly`
- `Quarterly`
- `Semiannual`
- `Annual`
- `Invoice Plan`

## High Confidence Mappings (10)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| Description__c | Description | textarea |
| Unit_Rate__c | UnitPrice | currency |
| Units__c | Quantity | double |
| Start_Date__c | ServiceDate | date |
| End_Date__c | EndDate | date |
| Amount__c | Total_MRC_Amortized__c | currency |
| PricebookEntryId__c | PricebookEntryId | string |
| MRC_COGS__c | Vendor_Fees_Monthly__c | currency |
| NRC_COGS__c | Vendor_NRC__c | currency |
| NRC__c | NRC_IRU_FEE__c | currency |

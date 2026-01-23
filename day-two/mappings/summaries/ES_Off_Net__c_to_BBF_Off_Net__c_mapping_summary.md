# Field Mapping Summary: Off_Net__c -> Off_Net__c

Generated: 2026-01-21 14:17:48
Source: `ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 33 |
| Fields with ES Match | 19 |
| Fields without ES Match | 14 |
| Transformers Needed | 12 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 15 | 45% |
| Medium | 4 | 12% |
| Low | 11 | 33% |
| None | 3 | 9% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 15 |
| Include: No | 0 |
| Include: TBD | 18 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 5 |
| Total Values | 74 |
| Exact Match | 24 |
| Close Match | 30 |
| No Match | 20 |

## Action Items

### Fields Needing Transformers (5)

- **Term__c** <- Term__c: picklist <- picklist
- **Off_Net_Service_Status__c** <- LEC_Order_Status__c: picklist <- picklist
- **Stripped_Circuit_ID__c** <- Stripped_Circuit_ID2__c: string <- textarea
- **Vendor_BAN__c** <- Vendor_Ban__c: string <- reference
- **Vendor_PON__c** <- VendorPON__c: string <- textarea

### Fields Pending Decision (18)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (4):**
- Off_Net_Original_Due_Date__c <- Vendor_FOC_Received__c
- Off_Net_Problem_Reason_Code__c <- Off_Net_Problem_Reason_Code__c
- Off_Net_Service_Status__c <- LEC_Order_Status__c
- Stripped_Circuit_ID__c <- Stripped_Circuit_ID2__c

**Low/No Confidence (14):**
- Aloc_COGS_Provider__c: A-Location COGS provider (reference vs text mismatch) | Data type conversion required
- Charge_Class__c: No semantic match found in BBF-specific field (likely BBF-only feature)
- Service_Order_Line__c: No semantic match found in BBF-specific field (likely BBF-only feature)
- Zloc_COGS_Provider__c: Z-Location COGS provider (reference vs text, accounts payable vendor) | Data type conversion required
- Off_Net_Expiration_Date__c: No semantic match found in BBF-specific field (likely BBF-only feature)
- Product__c: Large BBF product picklist (471 values) vs ES bandwidth picklist (43 values) | Picklist value mapping required
- Service_Type__c: Service type picklist (72 values) vs off-net type multipicklist (3 values) | Data type conversion required
- Additional_Information__c: Additional information text area (semantic match)
- BBF_Circuit_ID__c: BBF circuit ID (textarea truncation needed) | Data type conversion required
- Demarc_Location__c: Demarc location (typo in ES field, requires truncation) | Data type conversion required
- ... and 4 more

### Picklist Values Needing Mapping (20)

**Term__c:**
- `62`
- `MO`

**Bandwidth__c:**
- `30 Mb`
- `40 Mb`
- `60 Mb`
- `70 Mb`
- `80 Mb`
- ... and 10 more

**Off_Net_Type__c:**
- `Cross Connect`
- `Collocation`

**LEC_Order_Status__c:**
- `NOC Review`

## High Confidence Mappings (15)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| COGS_MRC__c | Cost_MRC__c | currency |
| COGS_NRC__c | Cost_NRC__c | currency |
| Disconnect_Date__c | Disconnect_Date__c | date |
| Off_Net_Circuit_ID__c | Vendor_circuit_Id__c | string |
| Off_Net_Service_Due_Date__c | Vendor_Due_date__c | date |
| Off_Net_Start_Date__c | Vendor_Bill_Start_Date__c | date |
| Term__c | Term__c | picklist |
| Approved_ETL_Disconnect_Date__c | Approved_ETL_Disconnect_Date__c | date |
| Disconnect_PON__c | Disconnect_PON__c | string |
| Disconnect_Submitted_Date__c | PM_Order_Completed__c | date |
| ETL_Amount_Approved__c | ETL_Amount_Approved__c | currency |
| Future_Disconnect_Date__c | Future_Disconnect_Date__c | date |
| Vendor_BAN__c | Vendor_Ban__c | string |
| Vendor_Order_Issued__c | Vendor_Order_Issued__c | date |
| Vendor_PON__c | VendorPON__c | string |

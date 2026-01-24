# Field Mapping Summary: Order -> Service__c

Generated: 2026-01-21 14:17:48
Source: `ES_Order_to_BBF_Service__c_mapping.xlsx`

## Overview

| Metric | Count |
|--------|-------|
| Total BBF Fields (for enrichment) | 113 |
| Fields with ES Match | 67 |
| Fields without ES Match | 46 |
| Transformers Needed | 26 |

## Match Confidence

| Confidence | Count | % |
|------------|-------|---|
| High | 41 | 36% |
| Medium | 26 | 23% |
| Low | 6 | 5% |
| None | 40 | 35% |

## Migration Decision Status

| Decision | Count |
|----------|-------|
| Include: Yes | 41 |
| Include: No | 0 |
| Include: TBD | 72 |

## Picklist Value Mappings

| Metric | Count |
|--------|-------|
| Picklist Fields | 4 |
| Total Values | 23 |
| Exact Match | 12 |
| Close Match | 10 |
| No Match | 1 |

## Action Items

### Fields Needing Transformers (23)

- **Circuit_Capacity__c** <- Service_Provided__c: string(255) <- double
- **Active_Date__c** <- ActivatedDate: date <- datetime
- **A_Node__c** <- Node__c: reference <- reference
- **PON__c** <- PON__c: string(100) <- textarea(255)
- **Bandwidth__c** <- Service_Provided__c: string(255) <- double
- **Change_Type__c** <- Order_Type_Data_Load__c: picklist <- multipicklist
- **Carrier_Code__c** <- Last_Mile_Carrier__c: string(255) <- reference
- **Service_Access_Build__c** <- Build_Type_Address_Z__c: string(50) <- picklist
- **Account_Manager__c** <- Sales_Rep__c: textarea(255) <- reference
- **Disconnect_Reason__c** <- End_Reason_Notes__c: textarea(255) <- textarea(8000)
- **Engineer__c** <- Service_Delivery_Manager__c: textarea(255) <- reference
- **OSP_Engineer__c** <- OSP_Engineer__c: textarea(255) <- reference
- **Order_Received_By__c** <- CreatedById: textarea(255) <- reference
- **Order_Received_Date__c** <- CreatedDate: date <- datetime
- **Outside_Plant_Required__c** <- OSP_Needed__c: textarea(255) <- boolean
- **Opportunity_Type__c** <- Service_Category_Multi__c: picklist <- multipicklist
- **Provisioned_By__c** <- Initially_Activated_By__c: textarea(255) <- reference
- **Replaced_By_Ckt_Code__c** <- Service_Order_Details_Replacing__c: textarea(255) <- string(1300)
- **Replacing_Ckt_Code__c** <- Service_Order_Agreement_Replacing__c: textarea(255) <- reference
- **Sales_Engineer__c** <- Sales_Rep__c: textarea(255) <- reference
- **Aloc_COGS_Provider__c** <- Last_Mile_Carrier__c: string(255) <- reference
- **Zloc_COGS_Provider__c** <- Last_Mile_Carrier__c: string(255) <- reference
- **Disconnect_Reason_Codes__c** <- Service_End_Reasons__c: picklist <- picklist

### Fields Pending Decision (72)

Fields with `Include_in_Migration = TBD` that need business review:

**Medium Confidence (26):**
- Customer_Circuit_Id__c <- Service_ID_Searchable__c
- A_Node__c <- Node__c
- Business_Unit__c <- Business_Sector__c
- Match_Key__c <- OrderNumber
- Change_Type__c <- Order_Type_Data_Load__c
- Carrier_Code__c <- Last_Mile_Carrier__c
- A_Handoff__c <- Design_Proposed_Facility_A__c
- Accepted_Date__c <- CompanyAuthorizedDate
- Account_Manager__c <- Sales_Rep__c
- Agent__c <- Referring_Vendor_Agent__c
- ... and 16 more

**Low/No Confidence (46):**
- Z_Node__c: Ring topology reference - may relate to Z Node in BBF architecture, needs validation
- Secondary_Circuit_Id__c: Order_Link__c may contain URL/reference to secondary order - needs parsing to extract circuit ID
- Contracted_Rate__c: No ES field for power/datacenter kWh rate - BBF specific field for colocation services
- ISP_WO__c: OSS_Order__c is operational support system order number - may relate to ISP work order
- Contracted_kW__c: No ES field for power capacity - BBF specific for colocation/datacenter power contracts
- OSP_WO__c: OSS_Order__c may track OSP work order - needs validation if OSS and OSP orders are same
- UNI_Ckt_Code__c: No clear ES field for UNI (User Network Interface) circuit code - BBF specific for Ethernet services
- Framing__c: No ES field for circuit framing (ESF, D4, etc.) - technical specification BBF tracks for legacy circuits
- Jurisdiction__c: No ES field for regulatory jurisdiction (Interstate, Intrastate, etc.) - BBF telecom regulatory field
- Line_Coding__c: No ES field for line coding (B8ZS, AMI, etc.) - technical T1/DS1 specification BBF tracks
- ... and 36 more

### Picklist Values Needing Mapping (1)

**Service_End_Reasons__c:**
- `Wholesale Customer`

## High Confidence Mappings (41)

| BBF Field | ES Field | Type |
|-----------|----------|------|
| Circuit_Code__c | OrderNumber | string(75) |
| ASRID__c | Service_ID__c | string(255) |
| TSP__c | TSP_Code__c | boolean |
| Circuit_Capacity__c | Service_Provided__c | string(255) |
| Active_Date__c | ActivatedDate | date |
| Comments__c | Notes__c | textarea(32768) |
| Disconnect_Date__c | Service_End_Date__c | date |
| PON__c | PON__c | string(100) |
| Product_Type__c | Primary_Product_Name__c | string(255) |
| Bandwidth__c | Service_Provided__c | string(255) |
| Unified_DB_Last_Synced_Date__c | Date_Synced_To_Billing__c | datetime |
| Contract_Effective_Date__c | EffectiveDate | date |
| Contract_Expiration_Date__c | Contract_End_Date_Est__c | date |
| Contract_Term__c | Service_Term_Months_Est__c | double |
| Off_Net_COGS__c | Total_Vendor_MRC_Offnet__c | currency |
| TSP_Code__c | TSP_Code_Value__c | string(50) |
| Service_Access_Build__c | Build_Type_Address_Z__c | string(50) |
| Activation_Notice_Date__c | Order_Completion_Notice_Sent__c | date |
| Last_Note__c | Last_Order_Comment__c | textarea(32768) |
| Disconnect_Reason__c | End_Reason_Notes__c | textarea(255) |
| ... | 21 more | ... |

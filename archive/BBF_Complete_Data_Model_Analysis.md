# BBF MIGRATION - QUICK REFERENCE SUMMARY

## Required Fields Per Object (Excludes System Fields & Booleans)

| Object | Required Refs | Required Fields | Total Optional | Priority |
|--------|--------------|----------------|----------------|----------|
| QuoteLineItem | 3 | 2 | 40 | 🔴 CRITICAL |
| BAN_Contact__c | 2 | 1 | 3 | 🟠 HIGH |
| PricebookEntry | 2 | 1 | 13 | 🟠 HIGH |
| BAN_Team__c | 1 | 2 | 1 | 🟡 MED |
| BAN__c | 1 | 5 | 62 | 🟡 MED |
| Charge__c | 1 | 3 | 15 | 🟡 MED |
| Opportunity_Site__c | 1 | 3 | 137 | 🟡 MED |
| Quote | 1 | 1 | 82 | 🟡 MED |
| Service_Charge__c | 1 | 2 | 30 | 🟡 MED |
| Service_Order_Line__c | 1 | 0 | 204 | 🟡 MED |
| Service__c | 1 | 0 | 188 | 🟡 MED |
| Account | 0 | 2 | 131 | 🟢 LOW |
| AccountPlan | 0 | 0 | 38 | 🟢 LOW |
| Contact | 0 | 1 | 55 | 🟢 LOW |
| Lead | 0 | 3 | 40 | 🟢 LOW |
| Location__c | 0 | 4 | 34 | 🟢 LOW |
| Node__c | 0 | 0 | 25 | 🟢 LOW |
| Off_Net__c | 0 | 3 | 12 | 🟢 LOW |
| Opportunity | 0 | 5 | 200 | 🟢 LOW |
| Optional_Products__c | 0 | 0 | 2 | 🟢 LOW |
| Pricebook2 | 0 | 0 | 1 | 🟢 LOW |
| Product2 | 0 | 0 | 15 | 🟢 LOW |
| Service_Category__c | 0 | 0 | 0 | 🟢 LOW |
| Service_Order__c | 0 | 0 | 57 | 🟢 LOW |
| Task | 0 | 2 | 51 | 🟢 LOW |

---

## Priority Legend

- **🟢 LOW** - No required references, can load any time
- **🟡 MED** - 1 required reference, simple dependency
- **🟠 HIGH** - 2 required references, moderate complexity
- **🔴 CRITICAL** - 3+ required references, load last

---

## Recommended Load Sequence

```
1. Pricebook2, Product2, Service_Category__c, Location__c
2. Node__c, PricebookEntry
3. Account, Contact, Lead
4. BAN__c
5. BAN_Contact__c, BAN_Team__c
6. Opportunity
7. Opportunity_Site__c, Quote
8. QuoteLineItem
9. Service_Order__c
10. Service_Order_Line__c
11. Charge__c
12. Service__c
13. Service_Charge__c, Off_Net__c
14. Task, AccountPlan, Optional_Products__c
```

---

## Critical Dependencies to Remember

### BAN_Contact__c
```
REQUIRES:
  - BAN__c (must exist)
  - Contact__c (must exist)
```

### QuoteLineItem
```
REQUIRES:
  - Quote (must exist)
  - PricebookEntry (must exist)
  - Product2 (must exist)
```

### Service__c
```
REQUIRES:
  - Billing_Account_Number__c (BAN__c or Account)
```

### Service_Charge__c
```
REQUIRES:
  - Service__c (must exist)
```
# BBF DATA MODEL - VISUAL HIERARCHY

## Complete Dependency Graph & Load Order

---

## MIGRATION LOAD ORDER

### 📊 Dependency Levels

### **WAVE 1: Foundation Objects** (No Required Dependencies)
```
┌─────────────────────────────────────────┐
│   FOUNDATION - Load First               │
├─────────────────────────────────────────┤
│  1. Pricebook2                          │
│  2. Product2                            │
│  3. Service_Category__c                 │
│  4. Location__c                         │
└─────────────────────────────────────────┘
```

**Why First:** These objects have NO required reference fields. Safe to load immediately.

### **WAVE 2: Infrastructure**
```
Node__c
  └──→ Location__c (optional)

PricebookEntry
  ├──→ Pricebook2 (required)
  └──→ Product2 (required)
```

### **WAVE 3: Core Business Objects**
```
Account
  └──→ Location__c (optional)

Contact
  └──→ Account (optional)

Lead
  └──→ (no required refs)
```

### **WAVE 4: Billing**
```
BAN__c
  ├──→ Account__c (REQUIRED) ⚠️
  └──→ Billing_Location__c (optional)

BAN_Contact__c
  ├──→ BAN__c (REQUIRED) ⚠️
  └──→ Contact__c (REQUIRED) ⚠️

BAN_Team__c
  └──→ BAN__c (REQUIRED) ⚠️
```

### **WAVE 5: Sales Pipeline**
```
Opportunity
  ├──→ Account (standard)
  ├──→ BAN__c (optional)
  └──→ Contact (optional)

Opportunity_Site__c
  ├──→ Opportunity__c (REQUIRED) ⚠️
  ├──→ Site__c/Location__c (optional)
  └──→ A_Node__c, Z_Node__c (optional)

Quote
  ├──→ Opportunity (REQUIRED) ⚠️
  └──→ Account, Contact (standard)

QuoteLineItem
  ├──→ Quote (REQUIRED) ⚠️
  ├──→ PricebookEntry (REQUIRED) ⚠️
  └──→ Product2 (REQUIRED) ⚠️
```

### **WAVE 6: Service Orders**
```
Service_Order__c
  ├──→ Account__c (optional)
  ├──→ BAN__c (optional)
  └──→ Opportunity__c (optional)

Service_Order_Line__c
  ├──→ Service_Order__c (REQUIRED) ⚠️
  └──→ Many optional references

Charge__c
  └──→ Service_Order_Line__c (REQUIRED) ⚠️
```

### **WAVE 7: Active Services**
```
Service__c
  ├──→ Billing_Account_Number__c (REQUIRED) ⚠️
  ├──→ Account__c (optional)
  ├──→ A_Location__c, Z_Location__c (optional)
  └──→ A_Node__c, Z_Node__c (optional)

Service_Charge__c
  ├──→ Service__c (REQUIRED) ⚠️
  └──→ Product__c (optional)

Off_Net__c
  └──→ Service__c (optional)
```

### **WAVE 8: Supporting Objects**
```
Task
  └──→ WhoId, WhatId (optional)

AccountPlan
  └──→ Account (standard)

Optional_Products__c
  └──→ (no required refs)
```

---

## COMPLETE DEPENDENCY MAP

### BAN_Contact__c
**Must load AFTER:**
- BAN__c (`BAN__c`)
- Contact__c (`Contact__c`)

### BAN_Team__c
**Must load AFTER:**
- BAN__c (`BAN__c`)

### BAN__c
**Must load AFTER:**
- Account__c (`Account__c`)

### Charge__c
**Must load AFTER:**
- Service_Order_Line__c (`Service_Order_Line__c`)

### Opportunity_Site__c
**Must load AFTER:**
- Opportunity__c (`Opportunity__c`)

### PricebookEntry
**Must load AFTER:**
- Pricebook2 (`Pricebook2Id`)
- Product2 (`Product2Id`)

### Quote
**Must load AFTER:**
- Opportunity (`OpportunityId`)

### QuoteLineItem
**Must load AFTER:**
- PricebookEntry (`PricebookEntryId`)
- Product2 (`Product2Id`)
- Quote (`QuoteId`)

### Service_Charge__c
**Must load AFTER:**
- Service__c (`Service__c`)

### Service_Order_Line__c
**Must load AFTER:**
- Service_Order__c (`Service_Order__c`)

### Service__c
**Must load AFTER:**
- Billing_Account_Number__c (`Billing_Account_Number__c`)

---

## KEY INSIGHTS

### Critical Path Objects (Block Other Objects)
These MUST be loaded early as many objects depend on them:

1. **Account** - Referenced by BAN__c, Opportunity, Quote, Service__c, Service_Order__c
2. **BAN__c** - Referenced by BAN_Contact__c, BAN_Team__c, Service__c, Opportunity
3. **Opportunity** - Referenced by Opportunity_Site__c, Quote, Service_Order__c
4. **Service_Order__c** - Referenced by Service_Order_Line__c, Charge__c
5. **Service__c** - Referenced by Service_Charge__c, Off_Net__c

### Objects with NO Required Dependencies
These can be loaded in any order (Wave 1):

- Pricebook2
- Product2
- Service_Category__c
- Location__c
- Node__c (optional ref to Location)
- Lead
- Task
- Optional_Products__c
# BBF SALESFORCE DATA MODEL HIERARCHY
## Complete Field Requirements & Load Order Analysis

**Source:** BBF_to_ES_Field_Mapping_Workbook - CG_12092025.xlsx
**Generated:** December 2024
**Purpose:** Define exact fields needed for each object and migration load order

---

## Summary Statistics

- **Total Objects:** 25
- **Total Required Reference Fields:** 15
- **Total Required Non-Reference Fields:** 40
- **Excluding:** System fields (CreatedDate, OwnerId, etc.) and Boolean fields

---

## OBJECT-BY-OBJECT FIELD REQUIREMENTS

### Account

**🟡 REQUIRED FIELDS (2)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Type` | Company Class | picklist |
| `Full_Company_Name__c` | Full Company Name | string |

**⚪ OPTIONAL REFERENCE FIELDS (8)** - Can populate later

- `proposalmanager__Billing_Contact__c` → proposalmanager__Billing_Contact__c
- `Billing_Location__c` → Billing_Location__c
- `Campaign__c` → Campaign__c
- `Location__c` → Location__c
- `MasterRecordId` → MasterRecord
- ... and 3 more optional references

**Total Required:** 2 fields (0 references + 2 standard)

---

### AccountPlan

**⚪ OPTIONAL REFERENCE FIELDS (3)** - Can populate later

- `AccountId` → Account
- `Last_Modified_By__c` → User
- `UserRecordAccessId` → User Record Access

✅ **No required fields** - Can insert with minimal data

---

### Contact

**🟡 REQUIRED FIELDS (1)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `LastName` | Last Name | string |

**⚪ OPTIONAL REFERENCE FIELDS (5)** - Can populate later

- `AccountId` → Account
- `rh2__Describe__c` → rh2__Describe__c
- `IndividualId` → Individual
- `MasterRecordId` → MasterRecord
- `ReportsToId` → ReportsTo

**Total Required:** 1 fields (0 references + 1 standard)

---

### Lead

**🟡 REQUIRED FIELDS (3)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Company` | Company | string |
| `LastName` | Last Name | string |
| `Status` | Status | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (8)** - Can populate later

- `Business_Partner__c` → Business_Partner__c
- `ConvertedAccountId` → ConvertedAccount
- `ConvertedContactId` → ConvertedContact
- `ConvertedOpportunityId` → ConvertedOpportunity
- `IndividualId` → Individual
- ... and 3 more optional references

**Total Required:** 3 fields (0 references + 3 standard)

---

### Location__c

**🟡 REQUIRED FIELDS (4)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `City__c` | City | string |
| `Region__c` | Region | picklist |
| `State__c` | State | string |
| `PostalCode__c` | Zip / Postal Code | string |

**⚪ OPTIONAL REFERENCE FIELDS (5)** - Can populate later

- `Market_Mapping_Name__c` → Market_Mapping_Name__c
- `ROE_Contact_Name_Lookup__c` → ROE_Contact_Name_Lookup__c
- `RecordTypeId` → RecordType
- `Ring__c` → Ring__c
- `Wire_Center__c` → Wire_Center__c

**Total Required:** 4 fields (0 references + 4 standard)

---

### Node__c

**⚪ OPTIONAL REFERENCE FIELDS (2)** - Can populate later

- `Location__c` → Location__c
- `VPRN__c` → VPRN__c

✅ **No required fields** - Can insert with minimal data

---

### Opportunity

**🟡 REQUIRED FIELDS (5)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `CloseDate` | Close Date | date |
| `ForecastCategory` | Forecast Category | picklist |
| `Opportunity_Number__c` | Opportunity Number | string |
| `Project__c` | Project # | string |
| `StageName` | Stage | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (28)** - Can populate later

- `AccountId` → Account
- `BAN__c` → BAN__c
- `Business_Partner__c` → Business_Partner__c
- `CampaignId` → Campaign
- `ContactId` → Contact
- ... and 23 more optional references

**Total Required:** 5 fields (0 references + 5 standard)

---

### Off_Net__c

**🟡 REQUIRED FIELDS (3)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Charge_Class__c` | Charge Class | picklist |
| `Product__c` | Product | picklist |
| `Service_Type__c` | Service Type | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (4)** - Can populate later

- `AA_Location__c` → AA_Location__c
- `Service__c` → Service__c
- `Service_Order_Line__c` → Service_Order_Line__c
- `ZZ_Location__c` → ZZ_Location__c

**Total Required:** 3 fields (0 references + 3 standard)

---

### Optional_Products__c

**⚪ OPTIONAL REFERENCE FIELDS (2)** - Can populate later

- `Product__c` → Product__c
- `Service_Category__c` → Service_Category__c

✅ **No required fields** - Can insert with minimal data

---

### Pricebook2

✅ **No required fields** - Can insert with minimal data

---

### Product2

**⚪ OPTIONAL REFERENCE FIELDS (4)** - Can populate later

- `ExternalDataSourceId` → ExternalDataSource
- `RecordTypeId` → RecordType
- `svcCategory__c` → svcCategory__c
- `udbChargeCode__c` → udbChargeCode__c

✅ **No required fields** - Can insert with minimal data

---

### Service_Category__c

✅ **No required fields** - Can insert with minimal data

---

### Service_Order__c

**⚪ OPTIONAL REFERENCE FIELDS (10)** - Can populate later

- `Account__c` → Account__c
- `BAN__c` → BAN__c
- `Customer_Contact__c` → Customer_Contact__c
- `DC_Engineer__c` → DC_Engineer__c
- `ISP_Engineer__c` → ISP_Engineer__c
- ... and 5 more optional references

✅ **No required fields** - Can insert with minimal data

---

### Task

**🟡 REQUIRED FIELDS (2)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Priority` | Priority | picklist |
| `Status` | Status | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (9)** - Can populate later

- `AccountId` → Account
- `WhoId` → Who
- `Opportunity__c` → Opportunity__c
- `RecurrenceActivityId` → RecurrenceActivity
- `Related_Service__c` → Related_Service__c
- ... and 4 more optional references

**Total Required:** 2 fields (0 references + 2 standard)

---

### BAN_Team__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `BAN__c` | BAN__c | reference |

**🟡 REQUIRED FIELDS (2)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Effective_Date__c` | Effective Date | date |
| `End_Date__c` | End Date | date |

**⚪ OPTIONAL REFERENCE FIELDS (1)** - Can populate later

- `User__c` → User__c

**Total Required:** 3 fields (1 references + 2 standard)

---

### BAN__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Account__c` | Account__c | reference |

**🟡 REQUIRED FIELDS (5)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `busUnit__c` | Business Unit | picklist |
| `Billing_City__c` | Billing City | string |
| `Billing_State__c` | Billing State | string |
| `Billing_Street__c` | Billing Street | string |
| `Billing_PostalCode__c` | Billing Zip/Postal Code | string |

**⚪ OPTIONAL REFERENCE FIELDS (11)** - Can populate later

- `BAN_Team_Leader__c` → BAN_Team_Leader__c
- `BAN_Team_Manager__c` → BAN_Team_Manager__c
- `BAN_Team_Person_1__c` → BAN_Team_Person_1__c
- `BAN_Team_Person_2__c` → BAN_Team_Person_2__c
- `BAN_Team_Person_3__c` → BAN_Team_Person_3__c
- ... and 6 more optional references

**Total Required:** 6 fields (1 references + 5 standard)

---

### Charge__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Service_Order_Line__c` | Service_Order_Line__c | reference |

**🟡 REQUIRED FIELDS (3)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Charge_Class__c` | Charge Class | picklist |
| `Product_Simple__c` | Product | picklist |
| `Service_Type_Charge__c` | Service Type Charge | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (3)** - Can populate later

- `Product__c` → Product__c
- `Off_Net__c` → Off_Net__c
- `RecordTypeId` → RecordType

**Total Required:** 4 fields (1 references + 3 standard)

---

### Opportunity_Site__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Opportunity__c` | Opportunity__c | reference |

**🟡 REQUIRED FIELDS (3)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `SD__c` | SD # | string |
| `Order_Type__c` | Service Access Build | picklist |
| `Service_Type__c` | Service Type | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (16)** - Can populate later

- `A_Node__c` → A_Node__c
- `Alternate_Local_Contact__c` → Alternate_Local_Contact__c
- `Z_Node__c` → Z_Node__c
- `ZZ_LOC_Alternate_Local_Contact__c` → ZZ_LOC_Alternate_Local_Contact__c
- `Local_Contact__c` → Local_Contact__c
- ... and 11 more optional references

**Total Required:** 4 fields (1 references + 3 standard)

---

### Quote

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `OpportunityId` | Opportunity | reference |

**🟡 REQUIRED FIELDS (1)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `QuoteNumber` | Quote Number | string |

**⚪ OPTIONAL REFERENCE FIELDS (5)** - Can populate later

- `AccountId` → Account
- `Approver__c` → Approver__c
- `ContactId` → Contact
- `ContractId` → Contract
- `Pricebook2Id` → Pricebook2

**Total Required:** 2 fields (1 references + 1 standard)

---

### Service_Charge__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Service__c` | Service__c | reference |

**🟡 REQUIRED FIELDS (2)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Product_Simple__c` | Product | picklist |
| `Service_Type_Charge__c` | Service Type Charge | picklist |

**⚪ OPTIONAL REFERENCE FIELDS (4)** - Can populate later

- `Charge__c` → Charge__c
- `Product__c` → Product__c
- `Off_Net__c` → Off_Net__c
- `Service_Order_Line_Charge__c` → Service_Order_Line_Charge__c

**Total Required:** 3 fields (1 references + 2 standard)

---

### Service_Order_Line__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Service_Order__c` | Service_Order__c | reference |

**⚪ OPTIONAL REFERENCE FIELDS (12)** - Can populate later

- `Provider__c` → Provider__c
- `Billing_Account_Number__c` → Billing_Account_Number__c
- `DC_Engineer__c` → DC_Engineer__c
- `Employee__c` → Employee__c
- `ISP_Engineer__c` → ISP_Engineer__c
- ... and 7 more optional references

**Total Required:** 1 fields (1 references + 0 standard)

---

### Service__c

**🔴 REQUIRED REFERENCE FIELDS (1)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Billing_Account_Number__c` | Billing_Account_Number__c | reference |

**⚪ OPTIONAL REFERENCE FIELDS (6)** - Can populate later

- `A_Location__c` → A_Location__c
- `A_Node__c` → A_Node__c
- `Account__c` → Account__c
- `Service_Order_Line__c` → Service_Order_Line__c
- `Z_Location__c` → Z_Location__c
- ... and 1 more optional references

**Total Required:** 1 fields (1 references + 0 standard)

---

### BAN_Contact__c

**🔴 REQUIRED REFERENCE FIELDS (2)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `BAN__c` | BAN__c | reference |
| `Contact__c` | Contact__c | reference |

**🟡 REQUIRED FIELDS (1)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `Role__c` | Role | multipicklist |

**Total Required:** 3 fields (2 references + 1 standard)

---

### PricebookEntry

**🔴 REQUIRED REFERENCE FIELDS (2)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `Pricebook2Id` | Pricebook2 | reference |
| `Product2Id` | Product2 | reference |

**🟡 REQUIRED FIELDS (1)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `UnitPrice` | List Price | currency |

**Total Required:** 3 fields (2 references + 1 standard)

---

### QuoteLineItem

**🔴 REQUIRED REFERENCE FIELDS (3)** - Must have parent IDs

| Field API Name | Parent Object | Field Type |
|----------------|---------------|------------|
| `PricebookEntryId` | PricebookEntry | reference |
| `Product2Id` | Product2 | reference |
| `QuoteId` | Quote | reference |

**🟡 REQUIRED FIELDS (2)** - Must populate

| Field API Name | Field Label | Field Type |
|----------------|-------------|------------|
| `LineNumber` | Line Item Number | string |
| `Quantity` | Quantity | double |

**⚪ OPTIONAL REFERENCE FIELDS (6)** - Can populate later

- `A_Location__c` → A_Location__c
- `OpportunityLineItemId` → OpportunityLineItem
- `Opportunity__c` → Opportunity__c
- `Service_Detail__c` → Service_Detail__c
- `Service_Option__c` → Service_Option__c
- ... and 1 more optional references

**Total Required:** 5 fields (3 references + 2 standard)

---

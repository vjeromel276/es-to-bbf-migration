# BBF Salesforce Data Model - Object Hierarchies & Relationships

## Executive Summary

BBF's Salesforce data model contains **interconnected object hierarchies** supporting:
1. **Sales Process** - Lead → Account → Opportunity → Quote → Service Order
2. **Multi-Site Management** - Opportunity → Opportunity_Site → Location/Node
3. **Billing Management** - Account → BAN (Billing Account Number) → Contacts
4. **Service Delivery** - Service Order → Service Order Lines → Services (Circuits)
5. **Network Infrastructure** - Location → Node → Service (A/Z endpoints)

---

## Primary Object Hierarchies

### 1. SALES HIERARCHY (Lead-to-Cash)

```
Lead
  └─ converts to ──→ Account + Contact + Opportunity
                           │         │           │
                           │         │           └─→ Quote
                           │         │                 │
                           │         │                 └─→ QuoteLineItem
                           │         │                       └─→ Product2
                           │         │                       └─→ A_Location__c (Location__c)
                           │         │                       └─→ Z_Location__c (Location__c)
                           │         │
                           │         └─→ Service_Order_Contact__c
                           │         └─→ Opportunity_Main_Contact__c
                           │         └─→ Opportunity_Engineering_Contact__c
                           │
                           └─→ BAN__c (Billing Account Number)
                                 └─→ BAN_Contact__c
                                       └─→ Contact
```

**Key Relationships:**
- **Lead** converts to **Account**, **Contact**, and **Opportunity** (standard Salesforce conversion)
- **Account** can have multiple **BANs** (for complex billing scenarios)
- **Opportunity** references **Account**, **Contact**, **BAN**, and optionally **Related_Opportunity__c**
- **Quote** is linked to **Opportunity**, **Account**, and **Contact**
- **QuoteLineItem** references **Quote**, **Opportunity**, **Product2**, and **A/Z Locations**

---

### 2. MULTI-SITE OPPORTUNITY STRUCTURE (Junction Pattern)

```
Opportunity
  │
  └─→ Opportunity_Site__c (JUNCTION OBJECT - Many Sites per Opp) AKA:Service Detail
        ├─→ Site__c (Location__c) - Z Location (destination)
        ├─→ A_Node__c (Node__c) - Network origin node
        ├─→ Z_Node__c (Node__c) - Network destination node
        ├─→ Local_Contact__c (Contact) - A Location contact
        ├─→ ZZ_LOC_Local_Contact__c (Contact) - Z Location contact
        ├─→ Parent_Service__c (Service__c) - Link to existing circuit
        └─→ Service__c (Service__c) - Link to provisioned circuit
```

**Purpose:** 
- Allows a single Opportunity to have multiple service locations
- Each site can have different bandwidth, equipment costs, OSP estimates
- Tracks A-to-Z connections (origin to destination) for fiber circuits
- Links to network infrastructure (Nodes) for each endpoint

**Critical Fields on Opportunity_Site__c:**
- Equipment_Costs__c
- Estimated_OSP_Cost__c (Outside Plant)
- Bandwidth_Size__c
- Service_Type__c
- OSP_Cost_Validated_with_OSP__c
- A/Z Node and Location references

---

### 3. SERVICE ORDER & PROVISIONING HIERARCHY

```
Opportunity (Closed Won)
  │
  └─→ Service_Order__c
        ├─→ Account__c
        ├─→ BAN__c (Billing Account Number)
        ├─→ Opportunity__c (back-reference)
        ├─→ Customer_Contact__c (Contact)
        └─→ Service_Order_Line__c (DETAIL RECORDS)
              ├─→ Service_Order__c (master-detail to Service Order)
              ├─→ Opportunity__c
              ├─→ Service__c (links to active circuit)
              ├─→ Billing_Account_Number__c
              ├─→ Provider__c (for off-net services)
              └─→ Charge__c (pricing details)
                    └─→ Product__c (Product2)
```

**Workflow:**
1. **Opportunity** wins → **Service_Order__c** created
2. **Service_Order_Line__c** records created for each service/circuit
3. Once provisioned → **Service__c** (active circuit) records created
4. **Service__c** links back to **Service_Order_Line__c**

**Key Status Fields:**
- Service_Order__c.Status__c (New, Submitted, In Progress, FOC Received, Active, etc.)
- Service_Order__c.ASRID__c (Access Service Request ID)
- Service_Order__c.Requested_Start_Date__c
- Service_Order__c.Service_Due_Date__c

---

### 4. ACTIVE SERVICES / CIRCUITS HIERARCHY

```
Service__c (Active Circuit)
  ├─→ Account__c
  ├─→ Billing_Account_Number__c (Account or BAN__c)
  ├─→ A_Location__c (Location__c) - Origin endpoint
  ├─→ Z_Location__c (Location__c) - Destination endpoint
  ├─→ A_Node__c (Node__c) - Network node at origin
  ├─→ Z_Node__c (Node__c) - Network node at destination
  ├─→ Service_Order_Line__c (link to provisioning record)
  └─→ Service_Charge__c (billing charges)
        ├─→ Service__c
        ├─→ Product__c (Product2)
        └─→ Off_Net__c (for carrier services)
              ├─→ Service__c
              ├─→ Service_Order_Line__c
              ├─→ AA_Location__c (Location__c)
              └─→ ZZ_Location__c (Location__c)
```

**Purpose:**
- **Service__c** represents ACTIVE circuits/services in production
- Tracks A-to-Z network topology
- Links to billing system via Circuit_Code__c and ASRID__c
- Contains revenue data (mrc__c, nrc__c, tax__c)

**Critical Fields:**
- Circuit_Code__c (unique identifier)
- ASRID__c (provisioning reference)
- Active_Date__c / Disconnect_Date__c
- Bandwidth__c, Circuit_Capacity__c
- mrc__c (Monthly Recurring Charges)
- Product_Type__c

---

### 5. BILLING ACCOUNT NUMBER (BAN) STRUCTURE

```
Account
  │
  └─→ BAN__c (Billing Account Number - custom object)
        ├─→ Account__c (parent account)
        ├─→ Billing_Location__c (Location__c)
        ├─→ BAN_Team_Leader__c (User)
        ├─→ BAN_Team_Manager__c (User)
        ├─→ BAN_Team_Person_1__c through 8 (Users) - Account team
        └─→ BAN_Contact__c (JUNCTION)
              ├─→ BAN__c
              └─→ Contact__c
```

**Purpose:**
- Separate billing entities under a single corporate account
- Example: Enterprise customer with multiple divisions, each billed separately
- Tracks billing team assignments
- Links multiple contacts to a BAN

**Usage in Other Objects:**
- Opportunity.BAN__c
- Service_Order__c.BAN__c
- Service__c.Billing_Account_Number__c (could be Account or BAN)

---

### 6. NETWORK INFRASTRUCTURE HIERARCHY

```
Location__c (Physical Address/Site)
  ├─→ Market_Mapping_Name__c
  ├─→ Wire_Center__c
  ├─→ Ring__c
  ├─→ ROE_Contact_Name_Lookup__c (Contact)
  └─→ Node__c (Network Node/POP at this location)
        ├─→ Location__c (back-reference)
        └─→ VPRN__c (Virtual Private Routed Network)

Account
  └─→ Location__c (primary location)
  └─→ Billing_Location__c (Location__c)

Opportunity_Site__c
  ├─→ Site__c (Location__c) - Z endpoint
  ├─→ A_Node__c (Node__c)
  └─→ Z_Node__c (Node__c)

Service__c (Circuit)
  ├─→ A_Location__c (Location__c)
  ├─→ Z_Location__c (Location__c)
  ├─→ A_Node__c (Node__c)
  └─→ Z_Node__c (Node__c)
```

**Purpose:**
- **Location__c** = Physical site/address where service can be delivered
- **Node__c** = Network equipment/POP (Point of Presence) at a location
- A/Z notation = Industry standard for circuit endpoints (A = origin, Z = destination)

**Key Fields:**
- Location__c: Street_Address__c, City__c, State__c, Latitude__c, Longitude__c
- Node__c: CLLI code equivalent, network identifiers

---

### 7. PRODUCT CATALOG HIERARCHY

```
Product2 (Standard Salesforce)
  ├─→ svcCategory__c (Service Category reference)
  ├─→ udbChargeCode__c (Unified DB charge code)
  └─→ RecordTypeId (different product types)

PricebookEntry
  ├─→ Product2Id
  └─→ Pricebook2Id

QuoteLineItem
  ├─→ Product2Id
  ├─→ PricebookEntryId
  └─→ QuoteId

Service_Order_Line__c
  └─→ Charge__c
        └─→ Product__c (Product2)

Service_Charge__c
  └─→ Product__c (Product2)

Optional_Products__c
  ├─→ Product__c (Product2)
  └─→ Service_Category__c
```

**Purpose:**
- Standard Salesforce product catalog
- Links to service categories for grouping
- Used in quotes and service orders
- Charge codes map to billing system (Unified DB)

---

## Key Junction Objects (Many-to-Many Relationships)

### 1. **Opportunity_Site__c**
**Connects:** Opportunity ←→ Location (Sites)
**Purpose:** Multi-site opportunities
**Record Count Expectation:** High (multiple sites per large deal)

### 2. **BAN_Contact__c**
**Connects:** BAN ←→ Contact
**Purpose:** Multiple billing contacts per BAN
**Record Count Expectation:** Medium

### 3. **Service_Order_Line__c**
**Connects:** Service_Order ←→ Service (and many other objects)
**Purpose:** Line items in service orders
**Record Count Expectation:** Very high (multiple lines per order)

---

## Critical Lookup Relationships by Object

### ACCOUNT
```
Account (Parent Object)
  ↓ referenced by
  ├─ Opportunity.AccountId
  ├─ Contact.AccountId
  ├─ Quote.AccountId
  ├─ Service_Order__c.Account__c
  ├─ Service__c.Account__c
  ├─ BAN__c.Account__c
  └─ Lead.ConvertedAccountId (after conversion)
```

### OPPORTUNITY
```
Opportunity (Parent Object)
  ↓ referenced by
  ├─ Opportunity_Site__c.Opportunity__c (MANY sites per opp)
  ├─ Quote.OpportunityId
  ├─ QuoteLineItem.Opportunity__c
  ├─ Service_Order__c.Opportunity__c
  ├─ Service_Order_Line__c.Opportunity__c
  └─ Lead.ConvertedOpportunityId (after conversion)

Opportunity (Child Object)
  ↑ references
  ├─ AccountId → Account
  ├─ ContactId → Contact (primary contact)
  ├─ BAN__c → BAN__c
  ├─ Related_Opportunity__c → Opportunity (self-reference)
  ├─ Quote__c → Quote
  ├─ Service_Order_Contact__c → Contact
  ├─ Opportunity_Main_Contact__c → Contact
  └─ Opportunity_Engineering_Contact__c → Contact
```

### LOCATION__c
```
Location__c (Parent Object)
  ↓ referenced by
  ├─ Node__c.Location__c (network node at this location)
  ├─ Account.Location__c (primary location)
  ├─ Account.Billing_Location__c
  ├─ BAN__c.Billing_Location__c
  ├─ Opportunity_Site__c.Site__c (Z endpoint)
  ├─ QuoteLineItem.A_Location__c
  ├─ QuoteLineItem.Z_Location__c
  ├─ Service__c.A_Location__c
  ├─ Service__c.Z_Location__c
  ├─ Off_Net__c.AA_Location__c
  └─ Off_Net__c.ZZ_Location__c
```

### NODE__c
```
Node__c (Parent Object)
  ↓ referenced by
  ├─ Opportunity_Site__c.A_Node__c
  ├─ Opportunity_Site__c.Z_Node__c
  ├─ Opportunity_Site__c.aNode__c
  ├─ Opportunity_Site__c.zNode__c
  ├─ Service__c.A_Node__c
  └─ Service__c.Z_Node__c

Node__c (Child Object)
  ↑ references
  └─ Location__c → Location__c (where node is physically located)
```

### SERVICE__c
```
Service__c (Parent Object)
  ↓ referenced by
  ├─ Opportunity_Site__c.Service__c
  ├─ Opportunity_Site__c.Parent_Service__c
  ├─ Service_Order_Line__c.Service__c
  ├─ Service_Charge__c.Service__c
  └─ Off_Net__c.Service__c

Service__c (Child Object)
  ↑ references
  ├─ Account__c → Account
  ├─ Billing_Account_Number__c → Account (or BAN__c)
  ├─ A_Location__c → Location__c
  ├─ Z_Location__c → Location__c
  ├─ A_Node__c → Node__c
  ├─ Z_Node__c → Node__c
  └─ Service_Order_Line__c → Service_Order_Line__c
```

### SERVICE_ORDER__c
```
Service_Order__c (Parent Object)
  ↓ referenced by
  └─ Service_Order_Line__c.Service_Order__c (MASTER-DETAIL)

Service_Order__c (Child Object)
  ↑ references
  ├─ Account__c → Account
  ├─ BAN__c → BAN__c
  ├─ Opportunity__c → Opportunity
  ├─ Related_Opportunity_Lookup__c → Opportunity
  └─ Customer_Contact__c → Contact
```

### BAN__c
```
BAN__c (Parent Object)
  ↓ referenced by
  ├─ BAN_Contact__c.BAN__c (junction to Contacts)
  ├─ Opportunity.BAN__c
  └─ Service_Order__c.BAN__c

BAN__c (Child Object)
  ↑ references
  ├─ Account__c → Account
  └─ Billing_Location__c → Location__c
```

---

## Data Model Patterns & Best Practices

### 1. **A/Z Endpoint Pattern** (Telecom Industry Standard)
Many objects use A-Location and Z-Location fields:
- **A** = Origin/Source endpoint
- **Z** = Destination endpoint
- Used in: Service__c, Opportunity_Site__c, QuoteLineItem, Off_Net__c

### 2. **Master-Detail Relationships**
Likely master-detail (not just lookup):
- Service_Order__c ←→ Service_Order_Line__c
- Quote ←→ QuoteLineItem
- Service__c ←→ Service_Charge__c

### 3. **Self-Referencing Lookups**
- Opportunity.Related_Opportunity__c → Opportunity (for renewals, upgrades)
- BAN__c.BAN_Team_Leader__c → BAN__c (team hierarchy)

### 4. **Multi-Contact Pattern**
Objects track multiple contact roles:
- Opportunity: Main Contact, Engineering Contact, Maintenance Contact, Service Order Contact
- Opportunity_Site__c: Local Contact, Alternate Local Contact (for both A and Z)

### 5. **Team Assignment Pattern**
BAN__c has extensive team fields:
- BAN_Team_Leader__c, BAN_Team_Manager__c
- BAN_Team_Person_1__c through BAN_Team_Person_8__c
- Allows complex account team structures

---

## Integration Points (External Systems)

### Unified DB References
Fields suggesting integration with external "Unified DB":
- Service_Order__c.Unified_DB_Status__c
- Service_Order__c.Unified_DB_Response__c
- Service__c.Unified_DB_Last_Synced_Date__c

### Business Central Integration
- Service_Order__c.Job_Number__c → "Job Number (Business Central WO #)"
- Suggests work order management integration

### TaskRay Integration
- Service_Order_Line__c.TaskRay_Principal_Template__c
- Project management/task tracking

---

## Record Type Usage

Objects with RecordTypeId (multiple record types):
- **Account** - Different account types (Customer, Partner, Prospect?)
- **Opportunity** - Different sales processes
- **Service_Order__c** - Different order types (New, Change, Disconnect?)
- **Location__c** - Different location types
- **Product2** - Different product categories
- **Charge__c** - Different charge types

---

## Data Volume Estimates (for Migration Planning)

Based on field complexity and relationships:

| Object | Estimated Complexity | Migration Priority |
|--------|---------------------|-------------------|
| Account | Medium | CRITICAL - Phase 1 |
| Contact | Low-Medium | CRITICAL - Phase 1 |
| Location__c | High | CRITICAL - Phase 1 |
| Node__c | Medium | HIGH - Phase 1 |
| Product2 | Medium | HIGH - Phase 1 |
| BAN__c | High | HIGH - Phase 2 |
| Lead | Low | MEDIUM - Phase 2 |
| Opportunity | Very High | CRITICAL - Phase 2 |
| Opportunity_Site__c | Very High | CRITICAL - Phase 2 |
| Quote | Medium | HIGH - Phase 2 |
| QuoteLineItem | High | HIGH - Phase 2 |
| Service_Order__c | Very High | CRITICAL - Phase 3 |
| Service_Order_Line__c | Very High | CRITICAL - Phase 3 |
| Service__c | Very High | CRITICAL - Phase 3 |
| Service_Charge__c | High | HIGH - Phase 3 |

---

## Migration Sequence (Recommended Load Order)

### Phase 1: Master Data
1. **Product2** (no dependencies except RecordType)
2. **Service_Category__c** (standalone)
3. **PricebookEntry** (needs Product2)
4. **Location__c** (can have self-references, load in batches)
5. **Node__c** (needs Location__c)
6. **Account** (can reference Location__c)
7. **Contact** (needs Account)

### Phase 2: Sales Data
8. **BAN__c** (needs Account, Location__c)
9. **BAN_Contact__c** (needs BAN__c, Contact)
10. **Lead** (needs Account/Contact for converted leads)
11. **Opportunity** (needs Account, Contact, BAN__c)
12. **Opportunity_Site__c** (needs Opportunity, Location__c, Node__c, Contact)
13. **Quote** (needs Opportunity, Account, Contact)
14. **QuoteLineItem** (needs Quote, Product2, Opportunity, Location__c)

### Phase 3: Service Delivery & Active Circuits
15. **Service_Order__c** (needs Account, Opportunity, BAN__c, Contact)
16. **Service_Order_Line__c** (needs Service_Order__c, Opportunity)
17. **Service__c** (needs Account, Location__c, Node__c, Service_Order_Line__c)
18. **Charge__c** (needs Service_Order_Line__c, Product2)
19. **Service_Charge__c** (needs Service__c, Product2)
20. **Off_Net__c** (needs Service__c, Service_Order_Line__c, Location__c)

---

## Critical Migration Considerations

### 1. **Circular References**
- Opportunity_Site__c references Service__c
- Service__c references Service_Order_Line__c
- **Solution:** Load in multiple passes, update lookups after initial load

### 2. **A/Z Location Integrity**
- MUST maintain A-Location/Z-Location pairings
- Critical for circuit routing and network topology
- **Validation:** Check all A/Z pairs exist before go-live

### 3. **BAN Complexity**
- Not all companies use separate BAN objects
- May need to flatten to Account hierarchy in target org
- **Decision needed:** Keep BAN__c or migrate to Account model

### 4. **Opportunity_Site Junction**
- Very customized junction object
- Check if target org has equivalent
- **Options:** 
  - Create in target org
  - Flatten to Opportunity (lose multi-site capability)
  - Use standard Address object

### 5. **External ID Strategy**
For migration, add External ID fields to match records:
- Account: Federal_Tax_ID__c or CLLI code
- Location__c: Concatenate address fields
- Service__c: Circuit_Code__c
- Service_Order__c: ASRID__c
- Node__c: Node name/CLLI

---

## Summary: Core Data Flows

### Sales Flow
```
Lead → Account + Contact → Opportunity → Opportunity_Site__c → Quote → Service_Order__c
         ↓                       ↓                                          ↓
       BAN__c                Location__c                            Service_Order_Line__c
                              + Node__c                                      ↓
                                                                        Service__c
```

### Network Topology Flow
```
Location__c → Node__c → Service__c (A_Node__c, Z_Node__c)
                             ↓
                   (A_Location__c, Z_Location__c)
```

### Billing Flow
```
Account → BAN__c → BAN_Contact__c → Contact
   ↓         ↓
Opportunity  Service_Order__c
   ↓              ↓
Quote      Service_Order_Line__c → Charge__c
   ↓              ↓                      ↓
QuoteLineItem   Service__c → Service_Charge__c
```

---

**Next Steps for Migration:**
1. Export ES's Salesforce field metadata with same script
2. Compare object names (Service__c vs Circuit__c vs ?)
3. Map lookup fields between orgs
4. Identify missing objects in ES org
5. Create field mapping spreadsheet with parent-child relationships
6. Plan for junction object handling (Opportunity_Site__c, BAN_Contact__c)


# BBF Salesforce Data Model - Quick Reference

## Main Object Relationships (Simplified)

### 1. SALES PROCESS HIERARCHY
```
┌─────────────────────────────────────────────────────────────────┐
│                        SALES PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘

Lead
  │
  ├─ converts to ──→ Account ←──────┐
  │                    │             │
  ├─ converts to ──→ Contact        │
  │                    │             │
  └─ converts to ──→ Opportunity ───┘
                        │
                        ├──→ Quote
                        │     └──→ QuoteLineItem
                        │           └──→ Product2
                        │
                        └──→ BAN__c (Billing Account)
                              └──→ BAN_Contact__c ──→ Contact
```

### 2. MULTI-SITE OPPORTUNITY (Junction Pattern)
```
┌─────────────────────────────────────────────────────────────────┐
│                   OPPORTUNITY → MULTIPLE SITES                  │
└─────────────────────────────────────────────────────────────────┘

Opportunity
  │
  └──→ Opportunity_Site__c (1 to MANY)
         │
         ├──→ Site__c (Location__c) ─────┐
         │                                │
         ├──→ A_Node__c (Node__c)         │ Network
         │                                │ Infrastructure
         ├──→ Z_Node__c (Node__c) ───────┘
         │
         ├──→ Local_Contact__c (Contact)
         │
         └──→ Service__c (Active Circuit)
```

### 3. SERVICE ORDER & PROVISIONING
```
┌─────────────────────────────────────────────────────────────────┐
│                   ORDER MANAGEMENT PROCESS                      │
└─────────────────────────────────────────────────────────────────┘

Opportunity (Closed Won)
  │
  └──→ Service_Order__c
         │
         ├──→ Account__c
         ├──→ BAN__c
         ├──→ Opportunity__c (back-ref)
         │
         └──→ Service_Order_Line__c (1 to MANY)
                │
                ├──→ Service_Order__c (parent)
                ├──→ Opportunity__c
                │
                ├──→ Charge__c
                │     └──→ Product__c (Product2)
                │
                └──→ Service__c (once provisioned)
```

### 4. ACTIVE CIRCUITS (A-to-Z Topology)
```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK CIRCUIT MODEL                        │
└─────────────────────────────────────────────────────────────────┘

Service__c (Active Circuit)
  │
  ├──→ Account__c ────────────────┐
  │                                │
  ├──→ Billing_Account_Number__c  │ Customer Info
  │                                │
  ├──→ Service_Order_Line__c ─────┘
  │
  ├──→ A_Location__c (Location__c) ──→ A_Node__c (Node__c)
  │                                        │
  │                                    [ORIGIN]
  │                                        │
  │                                   Fiber Path
  │                                        │
  │                                 [DESTINATION]
  │                                        │
  └──→ Z_Location__c (Location__c) ──→ Z_Node__c (Node__c)
  
  └──→ Service_Charge__c (billing)
         └──→ Product__c (Product2)
```

### 5. NETWORK INFRASTRUCTURE
```
┌─────────────────────────────────────────────────────────────────┐
│                  PHYSICAL NETWORK TOPOLOGY                      │
└─────────────────────────────────────────────────────────────────┘

Location__c (Physical Site/Address)
  │
  ├──→ Market_Mapping_Name__c
  ├──→ Wire_Center__c
  ├──→ Ring__c
  │
  └──→ Node__c (Network Equipment/POP at this location)
         │
         └──→ VPRN__c (Virtual Private Routed Network)

Referenced by:
  • Account (primary & billing locations)
  • BAN__c (billing location)
  • Opportunity_Site__c (A & Z endpoints)
  • Service__c (A & Z endpoints)
  • QuoteLineItem (A & Z locations)
  • Off_Net__c (carrier service endpoints)
```

---

## Key Lookup Relationships by Object

### ACCOUNT (Parent Object)
**Children Objects:**
- Contact (AccountId)
- Opportunity (AccountId)
- BAN__c (Account__c)
- Service_Order__c (Account__c)
- Service__c (Account__c)
- Quote (AccountId)

**Parent References:**
- Location__c (Location__c, Billing_Location__c)
- Contact (proposalmanager__Billing_Contact__c)

---

### OPPORTUNITY (Hub Object)
**Children Objects:**
- Opportunity_Site__c (Opportunity__c) ← MANY
- Quote (OpportunityId)
- QuoteLineItem (Opportunity__c)
- Service_Order__c (Opportunity__c)
- Service_Order_Line__c (Opportunity__c)

**Parent References:**
- Account (AccountId) ← REQUIRED
- Contact (ContactId, Service_Order_Contact__c, Opportunity_Main_Contact__c, Opportunity_Engineering_Contact__c)
- BAN__c (BAN__c)
- Opportunity (Related_Opportunity__c) ← SELF-REF
- Quote (Quote__c)

---

### LOCATION__c (Infrastructure Object)
**Children Objects:**
- Node__c (Location__c)
- Account (Location__c, Billing_Location__c)
- BAN__c (Billing_Location__c)
- Opportunity_Site__c (Site__c)
- Service__c (A_Location__c, Z_Location__c)
- QuoteLineItem (A_Location__c, Z_Location__c)
- Off_Net__c (AA_Location__c, ZZ_Location__c)

**Parent References:**
- Contact (ROE_Contact_Name_Lookup__c)

---

### SERVICE__c (Active Circuit Object)
**Children Objects:**
- Opportunity_Site__c (Service__c, Parent_Service__c)
- Service_Order_Line__c (Service__c)
- Service_Charge__c (Service__c)
- Off_Net__c (Service__c)

**Parent References:**
- Account (Account__c, Billing_Account_Number__c)
- Location__c (A_Location__c, Z_Location__c) ← A/Z ENDPOINTS
- Node__c (A_Node__c, Z_Node__c) ← A/Z NODES
- Service_Order_Line__c (Service_Order_Line__c)

---

### SERVICE_ORDER__c (Order Management Object)
**Children Objects:**
- Service_Order_Line__c (Service_Order__c) ← MASTER-DETAIL

**Parent References:**
- Account (Account__c)
- Opportunity (Opportunity__c, Related_Opportunity_Lookup__c)
- BAN__c (BAN__c)
- Contact (Customer_Contact__c)

---

### BAN__c (Billing Account Object)
**Children Objects:**
- BAN_Contact__c (BAN__c) ← JUNCTION
- Opportunity (BAN__c)
- Service_Order__c (BAN__c)

**Parent References:**
- Account (Account__c)
- Location__c (Billing_Location__c)
- User (BAN_Team_Leader__c, BAN_Team_Manager__c, BAN_Team_Person_1-8__c)

---

## Junction Objects (Many-to-Many)

### 1. Opportunity_Site__c
- **Left Side:** Opportunity (Opportunity__c)
- **Right Side:** Location (Site__c)
- **Also References:** Node__c (A & Z), Contact (multiple), Service__c
- **Purpose:** One Opportunity can have many Sites/Locations

### 2. BAN_Contact__c
- **Left Side:** BAN__c (BAN__c)
- **Right Side:** Contact (Contact__c)
- **Purpose:** One BAN can have many Contacts

### 3. Service_Order_Line__c
- **Master:** Service_Order__c (Service_Order__c)
- **Also References:** Opportunity, Service__c, multiple others
- **Purpose:** Line items in a service order

---

## Critical Fields by Object

### ACCOUNT
- Federal_Tax_ID__c (External ID candidate)
- proposalmanager__CLLI__c (Industry standard)
- Classification_account__c (Customer type)
- Contract_Type__c
- Location__c, Billing_Location__c

### OPPORTUNITY
- Total_MRC__c, Total_NRC__c (Revenue)
- COGS_MRC__c, COGS_NRC__c (Costs)
- TERM__c (Contract term)
- Classification__c (Service type)
- BAN__c (Billing account)

### OPPORTUNITY_SITE__c
- Opportunity__c, Site__c (Junction)
- A_Node__c, Z_Node__c (Network)
- Equipment_Costs__c
- Estimated_OSP_Cost__c
- Bandwidth_Size__c
- Service_Type__c

### SERVICE_ORDER__c
- ASRID__c (ASR ID - unique)
- Account__c, Opportunity__c, BAN__c
- Status__c (Workflow status)
- Total_MRC__c, Total_NRC__c
- Requested_Start_Date__c
- Service_Due_Date__c

### SERVICE_ORDER_LINE__c
- Service_Order__c (Master-detail parent)
- Opportunity__c
- Service__c (Active circuit link)
- Billing_Account_Number__c

### SERVICE__c
- Circuit_Code__c (Unique identifier)
- ASRID__c (Links to provisioning)
- Account__c, Billing_Account_Number__c
- A_Location__c, Z_Location__c (Endpoints)
- A_Node__c, Z_Node__c (Network nodes)
- Active_Date__c, Disconnect_Date__c
- mrc__c, nrc__c, tax__c (Billing)
- Bandwidth__c, Product_Type__c

### LOCATION__c
- Street_Address__c, City__c, State__c, ZipCode__c
- Latitude__c, Longitude__c (Geolocation)
- Market_Mapping_Name__c
- Wire_Center__c

### NODE__c
- Location__c (Where node is located)
- Name (Node identifier/CLLI)
- VPRN__c

### BAN__c
- Account__c (Parent account)
- Billing_Location__c
- Team assignment fields (8 team members)

---

## Data Model Complexity Ranking

| Object | Complexity | Custom Fields | Lookup Fields | Migration Priority |
|--------|-----------|---------------|---------------|-------------------|
| Service_Order_Line__c | ⭐⭐⭐⭐⭐ | 233 | 15 | CRITICAL |
| Opportunity | ⭐⭐⭐⭐⭐ | 240 | 31 | CRITICAL |
| Service__c | ⭐⭐⭐⭐⭐ | 196 | 9 | CRITICAL |
| Opportunity_Site__c | ⭐⭐⭐⭐⭐ | 184 | 19 | CRITICAL |
| Account | ⭐⭐⭐⭐ | 111 | 11 | CRITICAL |
| BAN__c | ⭐⭐⭐⭐ | 80 | 14 | HIGH |
| Service_Order__c | ⭐⭐⭐⭐ | 71 | 13 | CRITICAL |
| Contact | ⭐⭐⭐ | 23 | 8 | CRITICAL |
| Location__c | ⭐⭐⭐ | 43 | 8 | CRITICAL |
| Node__c | ⭐⭐ | 27 | 5 | HIGH |
| Lead | ⭐⭐ | 14 | 11 | MEDIUM |
| Quote | ⭐⭐⭐ | 33 | 9 | HIGH |

---

## Migration Load Sequence

**PHASE 1: Foundation (Master Data)**
1. Product2, Service_Category__c
2. Location__c ← No dependencies
3. Node__c ← Needs Location__c
4. Account ← Needs Location__c
5. Contact ← Needs Account

**PHASE 2: Sales Data**
6. BAN__c ← Needs Account, Location__c
7. BAN_Contact__c ← Needs BAN__c, Contact
8. Lead ← Can reference Account/Contact
9. Opportunity ← Needs Account, Contact, BAN__c
10. Opportunity_Site__c ← Needs Opportunity, Location__c, Node__c, Contact
11. Quote, QuoteLineItem ← Needs Opportunity, Product2, Location__c

**PHASE 3: Service Delivery**
12. Service_Order__c ← Needs Account, Opportunity, BAN__c, Contact
13. Service_Order_Line__c ← Needs Service_Order__c (master-detail)
14. Service__c ← Needs Account, Location__c, Node__c, Service_Order_Line__c
15. Charge__c, Service_Charge__c ← Needs Service__c, Product2
16. Off_Net__c ← Needs Service__c, Location__c

**Note:** Some objects have circular references and will need multi-pass loading.

---

## Key Questions for ES (Acquiring Company)

### Object Structure
1. Do you have an **Opportunity_Site__c** equivalent or handle multi-site opps differently?
2. Do you use a separate **BAN__c** object or just Account hierarchy?
3. What object do you use for active circuits? (Service__c, Circuit__c, Service_Instance__c?)
4. What's your service order object called? (Service_Order__c, Order__c, Provisioning_Order__c?)
5. How do you track network nodes/POPs? (Node__c equivalent?)

### Field Naming
6. What fields do you use for MRC/NRC? (Total_MRC__c, MRR__c, Monthly_Recurring_Revenue__c?)
7. How do you track A-Location/Z-Location on circuits?
8. What's your ASRID equivalent field name?
9. What's your Circuit ID field called?

### Process
10. What are your Opportunity stages?
11. What are your Service Order statuses?
12. How do you handle OSP (Outside Plant) cost tracking?
13. Do you integrate with an external "Unified DB" or billing system?

---

## Summary Statistics

- **Total Objects Analyzed:** 24
- **Total Custom Fields:** 1,447
- **Total Lookup/Reference Fields:** 274
- **Junction Objects:** 3 (Opportunity_Site__c, BAN_Contact__c, Service_Order_Line__c)
- **Core Master Data Objects:** 7 (Account, Contact, Location, Node, Product2, Service_Category, BAN)
- **Transactional Objects:** 8 (Opportunity, Quote, Service_Order, Service)
- **Supporting Objects:** 9 (various line items and charges)

---

**Files Generated:**
- `bbf_data_model_hierarchy.md` - Full documentation with all relationships
- `lookup_relationships.csv` - Complete list of all lookup fields
- `field_mapping_template.xlsx` - Template for mapping to ES org
- `object_summary.csv` - Object statistics

**Next Step:** Run the same export script on ES's Salesforce org to compare!

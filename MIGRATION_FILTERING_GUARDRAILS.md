# Migration Filtering Guardrails

Quick reference for data filtering logic across all ES-to-BBF migration notebooks.

**Last Synchronized:** 2026-01-23 (All 8 notebooks reviewed - duplicate prevention logic added)

## Overview

All migrations are driven by the **`BBF_Ban__c = true`** flag set during the prep phase.

The prep notebook (`00_uat_ban_prep.ipynb`) is the **single control point** that scopes the entire migration:
- It evaluates Orders against business rules
- Sets `BBF_Ban__c = true` on qualifying Billing_Invoice__c records
- All downstream migrations filter by this flag directly or indirectly

This approach ensures:
- Consistent filtering across all notebooks
- Single source of truth for what data migrates
- Easy to adjust scope by re-running prep with different criteria

## Duplicate Prevention Strategy (All Notebooks)

**As of 2026-01-23**, all migration notebooks implement duplicate prevention:

1. **Pre-Insert Check**: Before inserting records to BBF, query BBF for existing records with matching `ES_Legacy_ID__c`
2. **Sync Existing Records**: If records already exist in BBF, sync their BBF IDs back to ES (`ES.BBF_New_Id__c = BBF.Id`)
3. **Insert Only New**: Only insert records that don't already exist in BBF
4. **Idempotency**: Notebooks can be re-run safely without creating duplicates

**Benefits:**
- Safe re-runs after failures or partial migrations
- Resume migrations from where they left off
- Prevents duplicate record creation
- Maintains ES-to-BBF ID tracking even for pre-existing records

**Implementation Pattern (all notebooks):**
```python
# Step 1: Query BBF for existing records by ES_Legacy_ID__c
existing_bbf_records = bbf_sf.query(f"""
    SELECT Id, ES_Legacy_ID__c
    FROM {BBF_Object}
    WHERE ES_Legacy_ID__c IN ('{es_ids}')
""")

# Step 2: Sync BBF IDs back to ES for existing records
if existing_bbf_records:
    sync_updates = [{"Id": es_id, "BBF_New_Id__c": bbf_id}]
    es_sf.bulk.{ES_Object}.update(sync_updates)

# Step 3: Filter out already-migrated records, insert only new
new_records = [r for r in records if r['ES_Legacy_ID__c'] not in existing_ids]
bbf_sf.bulk.{BBF_Object}.insert(new_records)
```

## Central Policy Reminder

Only migrate data connected to **actively billing Orders** that meet ALL criteria:

| Filter | Criteria |
|--------|----------|
| Status | `IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')` |
| Project Group | `NOT LIKE '%PA MARKET DECOM%'` (exclude decommissioned markets) |
| BAN Flag | `Billing_Invoice__r.BBF_Ban__c = true` |

**NO ORPHAN DATA** - If it's not connected to a qualifying Order, it doesn't migrate.

---

## 00_uat_ban_prep.ipynb (BAN Prep - UAT Only)

**Purpose:** Mark ES BANs for migration by setting `BBF_Ban__c = true`

**SOQL Filter:**
```sql
SELECT Id, OrderNumber, Name, Service_ID__c,
       Status, Project_Group__c,
       Billing_Invoice__c, Billing_Invoice__r.Name, Billing_Invoice__r.Account__c,
       Billing_Invoice__r.Account__r.Name, Billing_Invoice__r.BBF_Ban__c,
       AccountId, Account.Name,
       Address_A__c, Address_A__r.Name,
       Address_Z__c, Address_Z__r.Name
FROM Order
WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
  AND (Project_Group__c = null OR (NOT Project_Group__c LIKE '%PA MARKET DECOM%'))
  AND Billing_Invoice__c != null
ORDER BY Billing_Invoice__r.Name
```

**Configuration Variables:**
```python
ACTIVE_STATUSES = ["Activated", "Suspended (Late Payment)", "Disconnect in Progress"]
WD_PROJECT_GROUP = "PA MARKET DECOM"  # Orders with this are EXCLUDED
DRY_RUN = False  # Set to False to actually update BANs
BAN_LIMIT = 20  # Max BANs to mark (0 = no limit)
MAX_ORDERS_PER_BAN = 5  # Max orders per BAN (0 = no limit) - keeps POC small
```

**Logic:**
1. Query all Orders meeting migration criteria (Active + NOT PA MARKET DECOM)
2. Extract unique Billing_Invoice__c (BAN) IDs from those Orders
3. Optionally filter BANs by order count (`MAX_ORDERS_PER_BAN`)
4. Optionally limit total BANs (`BAN_LIMIT`)
5. Update selected BANs: `BBF_Ban__c = true`

**Output:**
- Excel file with BAN IDs, Account IDs, Address IDs for downstream notebooks
- Updates ES Billing_Invoice__c records with `BBF_Ban__c = true`

**Notes:**
- **UAT Only** - Production uses `es_to_bbf_ban_creation_v12.ipynb` which creates -BBF BANs
- This mimics production prep without requiring OSS access
- All downstream notebooks filter by `BBF_Ban__c = true` set by this notebook

---

## 01_location_migration.ipynb

**Purpose:** Migrate ES Address__c → BBF Location__c

**SOQL Filter - Step 1 (Get Address IDs):**
```sql
SELECT Address_A__c, Address_Z__c
FROM Order
WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
  AND (Project_Group__c = null OR (NOT Project_Group__c LIKE '%PA MARKET DECOM%'))
  AND Billing_Invoice__r.BBF_Ban__c = true
  AND (Address_A__c != null OR Address_Z__c != null)
```

**SOQL Filter - Step 2 (Query Addresses):**
```sql
SELECT Id, Name,
       Address__c, City__c, State__c, County__c, Zip__c,
       Complete_Address__c, Clean_Street__c,
       Geocode_Lat_Long__c, Geocode_Lat_Long__Latitude__s, Geocode_Lat_Long__Longitude__s,
       CLLI__c, Building_Status__c, Building_Type__c,
       On_Net__c, NNI__c, Headend__c,
       Address_Type__c, Address_Status__c,
       Country__c, County_FIPS__c,
       RecordTypeId, OwnerId
FROM Address__c
WHERE Id IN ('{ids_from_step1}')
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL Locations
TEST_LIMIT = 10  # Only used when TEST_MODE = True
FILTER_BY_BBF_BAN = True  # Filter by Orders on BBF BANs (DEFAULT)
OWNER_ID = "005Ea00000ZOGFZIA5"
DEFAULT_BUS_UNIT = "EVS"
```

**BBF Field Mapping (Day 1):**
```python
bbf_location = {
    "Name": es_addr.get("Name", "Unknown Address")[:80],
    "Name_Is_Set_Manually__c": False,  # REQUIRED
    "City__c": es_addr.get("City__c"),
    "State__c": es_addr.get("State__c"),
    "County__c": es_addr.get("County__c"),
    "PostalCode__c": es_addr.get("Zip__c"),
    "Street__c": street,
    "Full_Address__c": full_address,
    "CLLICode__c": es_addr.get("CLLI__c"),
    "businessUnit__c": DEFAULT_BUS_UNIT,
    "OwnerId": OWNER_ID,
    "ES_Legacy_ID__c": es_addr["Id"]
}
```

**Logic:**
- Queries Orders with `BBF_Ban__c = true` on parent BAN
- Extracts unique Address_A__c and Address_Z__c IDs
- Queries Address__c records for those IDs (not yet migrated)
- **NEW: Checks BBF for existing Location__c by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated Addresses**
- Transforms to BBF Location__c schema
- Inserts only NEW Locations to BBF, updates ES with `BBF_New_Id__c`

**Parent Dependencies:** None (Location is standalone)

**Skip Conditions:**
- Address already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Address not found → SKIPPED (logged as error)

**Runtime Stats (POC):**
- 20 Orders → 31 unique Address IDs → 31 Locations migrated successfully

---

## 02_account_migration.ipynb

**Purpose:** Migrate ES Account → BBF Account

**SOQL Filter - Step 1 (Get Account IDs):**
```sql
SELECT Account__c
FROM Billing_Invoice__c
WHERE BBF_Ban__c = true
  AND Account__c != null
```

**SOQL Filter - Step 2 (Query Accounts):**
```sql
SELECT Id, Name, Type, BillingStreet, BillingCity, BillingState,
       BillingPostalCode, BillingCountry, Phone, Website, Industry,
       AnnualRevenue, NumberOfEmployees, Description,
       ShippingStreet, ShippingCity, ShippingState, ShippingPostalCode,
       ShippingCountry, AccountNumber, Site, TickerSymbol, Ownership,
       Rating, Sic, SicDesc
FROM Account
WHERE Id IN ('{ids_from_step1}')
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL accounts
TEST_LIMIT = 10  # Only used when TEST_MODE = True
FILTER_BY_BBF_BAN = True  # Filter by Accounts on BBF BANs (DEFAULT)
OWNER_ID = "005Ea00000ZOGFZIA5"
```

**BBF Field Mapping (Day 1):**
```python
bbf_account = {
    "Name": es_account.get("Name"),
    "Type": es_account.get("Type"),
    "BillingStreet": es_account.get("BillingStreet"),
    "BillingCity": es_account.get("BillingCity"),
    "BillingState": es_account.get("BillingState"),
    "BillingPostalCode": es_account.get("BillingPostalCode"),
    "BillingCountry": es_account.get("BillingCountry"),
    # ... (27 fields total mapped)
    "OwnerId": OWNER_ID,
    "ES_Legacy_ID__c": es_account["Id"]
}
```

**Logic:**
- Queries BANs with `BBF_Ban__c = true`
- Extracts unique Account__c IDs
- Queries Account records for those IDs (not yet migrated)
- **NEW: Checks BBF for existing Accounts by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated Accounts**
- Transforms to BBF Account schema
- Inserts only NEW Accounts to BBF in batches of 10 (to avoid CPQ trigger limits)
- Updates ES with `BBF_New_Id__c`

**Parent Dependencies:** None (Account is root object)

**Skip Conditions:**
- Account already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Duplicate Account detected by BBF → FAILED (logged with error)

**Runtime Stats (POC):**
- 20 BANs → 20 unique Account IDs → 19 Accounts migrated, 1 blocked by duplicate detection

---

## 03_contact_migration.ipynb

**Purpose:** Migrate ES Contact → BBF Contact

**SOQL Filter:**
```sql
SELECT Id, AccountId, Account.BBF_New_Id__c,
       FirstName, LastName, Email, Phone, Title,
       MailingStreet, MailingCity, MailingState, MailingPostalCode, MailingCountry,
       OtherStreet, OtherCity, OtherState, OtherPostalCode, OtherCountry,
       MobilePhone, HomePhone, Fax,
       Department, Description, Birthdate,
       AssistantName, AssistantPhone, LeadSource
FROM Contact
WHERE Account.BBF_New_Id__c != null
  AND Account.BBF_New_Id__c != ''
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL contacts
TEST_LIMIT = 10  # Only used when TEST_MODE = True
OWNER_ID = "005Ea00000ZOGFZIA5"
```

**BBF Field Mapping (Day 1):**
```python
bbf_contact = {
    "AccountId": bbf_account_id,  # From Account.BBF_New_Id__c
    "FirstName": es_contact.get("FirstName"),
    "LastName": es_contact.get("LastName"),
    "Email": es_contact.get("Email"),
    "Phone": es_contact.get("Phone"),
    # ... (27 fields total mapped)
    "OwnerId": OWNER_ID,
    "ES_Legacy_ID__c": es_contact["Id"]
}
```

**Logic:**
- Queries Contacts where parent Account has `BBF_New_Id__c` (Account migrated)
- **NEW: Checks BBF for existing Contacts by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated Contacts**
- Maps to BBF Account ID via `Account.BBF_New_Id__c`
- Inserts only NEW Contacts to BBF, updates ES with `BBF_New_Id__c`

**Parent Dependencies:**
- **REQUIRED:** Account must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Account not migrated (`BBF_New_Id__c = null`) → NEVER QUERIED (implicit skip)
- Contact already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing required field (LastName) → FAILED

**Runtime Stats (POC):**
- 19 migrated Accounts → 193 Contacts queried → 192 Contacts migrated, 1 blocked by duplicate detection

---

## 04_ban_migration.ipynb

**Purpose:** Migrate ES Billing_Invoice__c → BBF BAN__c

**SOQL Filter:**
```sql
SELECT Id, Name, Account__c, Account__r.BBF_New_Id__c, Account__r.Name,
       Account_Number__c, Account_Name__c,
       Billing_Address_1__c, Billing_Address_2__c,
       Billing_City__c, Billing_State__c, Billing_ZIP__c,
       Billing_E_mail__c, Additional_Emails__c,
       Payment_Terms__c, Invoice_Delivery_Preference__c, Invoice_cycle_cd__c,
       Disable_Late_Fees__c, Late_Fee_Percentage__c,
       Suppress_Invoice_Generation__c, Suppress_Past_Due_Notifications__c,
       Address_Verified__c, Address_Verified_On__c, AddressReturnCode__c,
       Disabled__c, Description__c, Billing_Notes__c,
       Automatic_Bill_Payment_Authorized__c,
       Detailed_Tax_Breakout__c, Sent_to_Third_party__c,
       AP_Contact__c, BBF_Ban__c
FROM Billing_Invoice__c
WHERE BBF_Ban__c = true
  AND Account__r.BBF_New_Id__c != null
  AND Account__r.BBF_New_Id__c != ''
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL BANs
TEST_LIMIT = 10  # Only used when TEST_MODE = True
OWNER_ID = "005Ea00000ZOGFZIA5"
DEFAULT_BUS_UNIT = "EVS"
PAYMENT_TERMS_MAP = {
    "NET30": "NET 30",
    "NET45": "NET 45",
    "NET60": "NET 60",
    "NET30,NET45,NET60 (default)": "NET 30",
    "Due On Receipt": "Due On Receipt"
}
```

**BBF Field Mapping (Day 1):**
```python
bbf_ban = {
    "Account__c": bbf_account_id,  # From Account.BBF_New_Id__c
    "busUnit__c": DEFAULT_BUS_UNIT,  # REQUIRED picklist
    "Name": "EV-" + es_ban.get("Name"),
    "Billing_Street__c": billing_street,
    "Billing_City__c": es_ban.get("Billing_City__c"),
    "Billing_State__c": es_ban.get("Billing_State__c"),
    "Billing_PostalCode__c": es_ban.get("Billing_ZIP__c"),
    "Billing_Company_Name__c": es_ban.get("Account_Name__c"),
    "BAN_Description__c": es_ban.get("Description__c"),
    "Payment_Terms__c": bbf_payment_terms,  # Translated
    "General_Description__c": es_ban.get("Billing_Notes__c"),
    "ES_Legacy_ID__c": es_ban["Id"]
}
```

**Logic:**
- Queries BANs with `BBF_Ban__c = true`
- ONLY includes BANs where parent Account migrated
- **NEW: Checks BBF for existing BANs by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated BANs**
- Translates Payment Terms (NET30 → NET 30, etc.)
- Skips BANs with invalid Payment Terms values
- Inserts only NEW BANs to BBF, updates ES with `BBF_New_Id__c`

**Parent Dependencies:**
- **REQUIRED:** Account must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Account not migrated → NEVER QUERIED (implicit skip)
- BAN already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Invalid Payment Terms value → SKIPPED (logged as error)

**Runtime Stats (POC):**
- 19 migrated Accounts → 19 BANs queried → 17 BANs migrated, 2 failed (invalid Payment Terms)

---

## 05_service_migration.ipynb

**Purpose:** Migrate ES Order → BBF Service__c

**SOQL Filter:**
```sql
SELECT Id,
    Billing_Invoice__r.BBF_New_Id__c,
    Address_A__c, Address_A__r.BBF_New_Id__c,
    Address_Z__c, Address_Z__r.BBF_New_Id__c
FROM Order
WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
AND (Project_Group__c = null OR (NOT Project_Group__c LIKE '%PA MARKET DECOM%'))
AND Service_Order_Record_Type__c = 'Service Order Agreement'
AND Billing_Invoice__r.BBF_New_Id__c != null
AND Billing_Invoice__r.BBF_New_Id__c != ''
AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL Services
TEST_LIMIT = 10  # Only used when TEST_MODE = True
OWNER_ID = "005Ea00000ZOGFZIA5"  # Not used - Service__c has no OwnerId
DEFAULT_BUS_UNIT = "EVS"  # Not used - Service__c has no busUnit__c
```

**BBF Field Mapping (Day 1 - Required Fields Only):**
```python
# Step 1: Initial insert with Master-Detail only
bbf_service = {
    "Billing_Account_Number__c": bbf_ban_id,  # Master-Detail to BAN__c (REQUIRED)
    "ES_Legacy_ID__c": es_order["Id"]         # Tracking field
}

# Optional: Location lookups (if migrated)
if bbf_a_location:
    bbf_service["A_Location__c"] = bbf_a_location
if bbf_z_location:
    bbf_service["Z_Location__c"] = bbf_z_location
```

**Account Population (Post-Insert Step):**
```sql
-- Step 2: Query Services with BAN relationship
SELECT Id, Billing_Account_Number__c, Billing_Account_Number__r.Account__c, Account__c
FROM Service__c
WHERE ES_Legacy_ID__c != null AND Account__c = null

-- Step 3: Update Services with Account from BAN
UPDATE Service__c SET Account__c = BAN.Account__c
```

**Logic:**
1. Queries Orders with full criteria (Active + NOT PA MARKET DECOM)
2. REQUIRES parent BAN migrated (Master-Detail - BLOCKING)
3. Optionally includes Location lookups if migrated
4. **NEW: Checks BBF for existing Services by ES_Legacy_ID__c**
5. **NEW: Syncs ES.BBF_New_Id__c for already-migrated Services**
6. Inserts only NEW Services with Billing_Account_Number__c (master-detail) + ES_Legacy_ID__c
7. Updates ES Orders with `BBF_New_Id__c`
8. Queries Services and populates Account__c from BAN.Account__c relationship
9. Updates Services with Account__c

**Fields NOT Set (Why):**
- Name: Autonumber (auto-generated by BBF)
- OwnerId: Service__c doesn't have this field
- All boolean fields: Default to False
- Optional fields: Status, Circuit_ID, MRC, NRC, Bandwidth, etc. (Day 2+ enrichment)

**Parent Dependencies:**
- **REQUIRED (Master-Detail):** BAN must have `BBF_New_Id__c`
- **OPTIONAL:** Location_A and Location_Z (if available)

**Skip Conditions:**
- Parent BAN not migrated → NEVER QUERIED (implicit skip)
- Service already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing Master-Detail BAN__c → FAILED (Salesforce blocks insert)

**Runtime Stats (POC):**
- 17 migrated BANs → 17 Orders queried → 17 Services migrated successfully

---

## 06_service_charge_migration.ipynb

**Purpose:** Migrate ES OrderItem → BBF Service_Charge__c

**SOQL Filter:**
```sql
SELECT Id, Order.BBF_New_Id__c
FROM OrderItem
WHERE Order.BBF_New_Id__c != null
AND Order.BBF_New_Id__c != ''
AND Order.Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
AND (Order.Project_Group__c = null OR (NOT Order.Project_Group__c LIKE '%PA MARKET DECOM%'))
AND Order.Service_Order_Record_Type__c = 'Service Order Agreement'
AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL Service Charges
TEST_LIMIT = 10  # Only used when TEST_MODE = True
OWNER_ID = "005Ea00000ZOGFZIA5"  # Not used - Service_Charge__c has no OwnerId
PLACEHOLDER_PRODUCT = "ANNUAL"  # Temporary placeholder until business provides mapping
PLACEHOLDER_SERVICE_TYPE = "Power"  # Temporary placeholder until business provides mapping
```

**BBF Field Mapping (Day 1 - Required Fields + Placeholders):**
```python
bbf_service_charge = {
    "Service__c": bbf_service_id,                    # Master-Detail to Service__c (REQUIRED)
    "Product_Simple__c": PLACEHOLDER_PRODUCT,        # PLACEHOLDER - to be enriched
    "Service_Type_Charge__c": PLACEHOLDER_SERVICE_TYPE,  # PLACEHOLDER - to be enriched
    "ES_Legacy_ID__c": es_orderitem["Id"]            # Tracking field
}
```

**Placeholder Value Strategy:**
- **Product_Simple__c = "ANNUAL"** - Temporary value, will be updated via enrichment
- **Service_Type_Charge__c = "Power"** - Temporary value, will be updated via enrichment
- **Rationale:** ES Product → BBF Product mapping not ready yet; use placeholders for Day 1, enrich later
- **Enrichment Tool:** Run `08_es_product_mapping_export.ipynb` to export ES products for mapping analysis
- **Day 2:** Update placeholder values with actual mappings once business provides them

**Logic:**
- Queries OrderItems where parent Order migrated (Service exists)
- Order must have `BBF_New_Id__c` (proof of Service migration)
- **NEW: Checks BBF for existing Service_Charges by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated Service_Charges**
- Inserts only NEW Service_Charges with PLACEHOLDER values for required picklist fields
- Updates ES with `BBF_New_Id__c`

**Fields NOT Set (Why):**
- Name: Autonumber (auto-generated by BBF)
- OwnerId: Service_Charge__c doesn't have this field
- All boolean fields: Default to False (11 boolean fields omitted)
- Optional fields: Description, Amount, Unit_Rate, Start_Date, etc. (Day 2+ enrichment)

**Parent Dependencies:**
- **REQUIRED (Master-Detail):** Service (Order) must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Service not migrated → NEVER QUERIED (implicit skip)
- Charge already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing Master-Detail Service__c → FAILED (Salesforce blocks insert)

**Runtime Stats (POC):**
- 17 migrated Services → 44 OrderItems queried → 44 Service_Charges migrated successfully

---

## 07_offnet_migration.ipynb

**Purpose:** Migrate ES Off_Net__c → BBF Off_Net__c

**SOQL Filter:**
```sql
SELECT Id, Name,
    SOF1__c, SOF1__r.BBF_New_Id__c, SOF1__r.OrderNumber,
    Location_1__c, Location_1__r.BBF_New_Id__c,
    Location_2__c, Location_2__r.BBF_New_Id__c
FROM Off_Net__c
WHERE SOF1__c != null
  AND SOF1__r.BBF_New_Id__c != null
  AND SOF1__r.BBF_New_Id__c != ''
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Configuration Variables:**
```python
TEST_MODE = False  # Set to False to migrate ALL Off-Net records
TEST_LIMIT = 10  # Only used when TEST_MODE = True
OWNER_ID = "005Ea00000ZOGFZIA5"  # ONLY required field
```

**BBF Field Mapping (Day 1 - Required Fields Only):**
```python
bbf_offnet = {
    "OwnerId": OWNER_ID,                # Owner (REQUIRED - ONLY required field)
    "ES_Legacy_ID__c": es_offnet["Id"]  # Tracking field
}

# Optional: Service lookup (if Order migrated)
if bbf_service_id:
    bbf_offnet["Service__c"] = bbf_service_id

# Optional: Location lookups (if migrated)
if bbf_aa_location:
    bbf_offnet["AA_Location__c"] = bbf_aa_location
if bbf_zz_location:
    bbf_offnet["ZZ_Location__c"] = bbf_zz_location
```

**Key Relationship Change:**
- **OLD (DEPRECATED):** `Implementation__c` → `IMPLEMENTATION_Project__c` (not the Order!)
- **NEW (CORRECT):** `SOF1__c` → Order object (links directly to the Order)
- **Service Population:** Off_Net__c.Service__c populated from `SOF1__r.BBF_New_Id__c` (Order's BBF Service ID)

**Logic:**
- Queries Off_Net__c records where `SOF1__c` (Order) migrated
- Order must have `BBF_New_Id__c` (proof of Service migration)
- **NEW: Checks BBF for existing Off_Net records by ES_Legacy_ID__c**
- **NEW: Syncs ES.BBF_New_Id__c for already-migrated Off_Net records**
- Populates Service__c from Order.BBF_New_Id__c
- Optionally includes Location lookups if migrated
- Inserts only NEW Off_Net records to BBF, updates ES with `BBF_New_Id__c`

**Fields NOT Set (Why):**
- Name: Autonumber (auto-generated by BBF)
- All optional fields: AA_Location__c, ZZ_Location__c, Circuit_ID, COGS, Vendor details, dates (Day 2+ enrichment)

**Parent Dependencies:**
- **REQUIRED (Filter):** Service (SOF1__c Order) must have `BBF_New_Id__c`
- **OPTIONAL:** Location_1 and Location_2 (if available)

**Skip Conditions:**
- Parent Service not migrated → NEVER QUERIED (implicit skip)
- Off_Net already migrated (`BBF_New_Id__c != null`) → SKIPPED

**Runtime Stats (POC):**
- 17 migrated Services → 6 Off_Net records queried → 6 Off_Net records migrated successfully

---

## 08_es_product_mapping_export.ipynb (Export Tool - Not a Migration)

**Purpose:** Export ES Products for mapping analysis (NOT a migration notebook)

**SOQL Filter:**
```sql
SELECT Order.Id, Order.OrderNumber, Order.Name, Order.Status, Order.Billing_Invoice__c,
       Id, Total_MRC_Amortized__c, NRC_IRU_FEE__c, UnitPrice, TotalPrice,
       Product2.ProductCode, Product2.Family, Product2.Name
FROM OrderItem
WHERE Order.Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
  AND (Order.Project_Group__c = null OR (NOT Order.Project_Group__c LIKE '%PA MARKET DECOM%'))
  AND Order.Service_Order_Record_Type__c = 'Service Order Agreement'
  AND Order.Billing_Invoice__c != null
ORDER BY Order.OrderNumber
```

**Purpose:**
- Exports all active OrderItems with Product2 details
- Provides data for business to build ES Product → BBF Product mapping
- Outputs CSV file with unique product families and product names
- Analysis summary shows top products by volume

**Output:**
- CSV file: `es_active_orders_products_{YYYYMMDD}_{HHMMSS}.csv`
- Console analysis: Unique product families, top 30 products, total counts

**Usage:**
- Run against ES PRODUCTION (not UAT) to get complete product catalog
- Share CSV with business stakeholders for mapping decisions
- Use mapping results to update Service_Charge enrichment logic

**NOT Part of Migration Pipeline:**
- This is a data export tool, not a migration notebook
- Run separately to prepare for Service_Charge enrichment
- Does not modify any records

---

## Cascade Effect Diagrams

### Scenario 1: Account Migration Fails

```
Account BLOCKED (no BBF_New_Id__c)
    ├── Location: ✅ Still migrates (no Account dependency)
    ├── Contact: ⏭️ SKIPPED (never queried)
    ├── BAN: ⏭️ SKIPPED (never queried)
    │   └── Service: ⏭️ SKIPPED (never queried)
    │       ├── Service_Charge: ⏭️ SKIPPED (never queried)
    │       └── Off_Net: ⏭️ SKIPPED (never queried)
```

**Impact:** Entire customer hierarchy blocked except Locations

**Mitigation:** Fix Account issue (duplicate detection, missing field) and re-run from 02_account_migration forward

---

### Scenario 2: BAN Migration Fails

```
Account: ✅ Migrated
    ├── Location: ✅ Migrated (no Account dependency)
    ├── Contact: ✅ Migrated (Account OK)
    ├── BAN: ❌ FAILED (no BBF_New_Id__c)
    │   └── Service: ⏭️ SKIPPED (never queried - no BAN)
    │       ├── Service_Charge: ⏭️ SKIPPED (never queried)
    │       └── Off_Net: ⏭️ SKIPPED (never queried)
```

**Impact:** Customer meta-data migrated, but all billing/service data blocked

**Mitigation:** Fix BAN issue and re-run from 04_ban_migration forward

---

### Scenario 3: Service Migration Fails

```
Account: ✅ Migrated
BAN: ✅ Migrated
Location: ✅ Migrated
Service: ❌ FAILED (no BBF_New_Id__c)
    ├── Service_Charge: ⏭️ SKIPPED (never queried)
    └── Off_Net: ⏭️ SKIPPED (never queried)
```

**Impact:** Customer infrastructure migrated, but specific Service and its children blocked

**Mitigation:** Fix Service issue and re-run from 05_service_migration forward

---

## Key Fields Reference

### ES Org Fields (Source)

| Field | Object | Type | Purpose |
|-------|--------|------|---------|
| `BBF_Ban__c` | Billing_Invoice__c | Checkbox | **MASTER FLAG** - Set by prep notebook to mark BANs for migration |
| `BBF_New_Id__c` | All objects | Text(18) | Stores BBF SFID after successful migration (bidirectional tracking) |
| `Account__c` | Billing_Invoice__c | Lookup | Links BAN to Account |
| `Address_A__c` | Order | Lookup | Links Service to A-side Location |
| `Address_Z__c` | Order | Lookup | Links Service to Z-side Location |
| `Billing_Invoice__c` | Order | Lookup | Links Service to BAN |
| `SOF1__c` | Off_Net__c | Lookup | Links Off-Net to Order (correct relationship) |
| `Implementation__c` | Off_Net__c | Lookup | DEPRECATED - links to Project, not Order |

### BBF Org Fields (Target)

| Field | Object | Type | Purpose |
|-------|--------|------|---------|
| `ES_Legacy_ID__c` | All objects | Text(18) | Stores original ES SFID for tracking and deduplication |
| `Billing_Account_Number__c` | Service__c | Master-Detail | **REQUIRED** - Links Service to BAN |
| `Service__c` | Service_Charge__c | Master-Detail | **REQUIRED** - Links Charge to Service |
| `Service__c` | Off_Net__c | Lookup | Links Off-Net to Service |
| `Account__c` | Service__c | Lookup | Links Service to Account (populated post-insert from BAN) |
| `busUnit__c` | BAN__c | Picklist | Set to 'EVS' for all EverStream BANs |
| `Name_Is_Set_Manually__c` | Location__c | Boolean | **REQUIRED** - Set to False for migrated Locations |

---

## Execution Checklist

Use this checklist for Day 1 production migration:

### Pre-Migration

- [ ] ES Production credentials configured in `.env`
- [ ] BBF Production credentials configured in `.env`
- [ ] All notebooks tested successfully in sandbox
- [ ] Excel outputs reviewed and approved
- [ ] Backup plan documented
- [ ] Rollback plan documented
- [ ] Product mapping export completed (08)
- [ ] Business provided ES → BBF product mappings

### Execution Order

- [ ] **00_uat_ban_prep.ipynb** (UAT only - marks BANs with `BBF_Ban__c = true`)
  - OR for production: `es_to_bbf_ban_creation_v12.ipynb` (creates -BBF BANs)
- [ ] **01_location_migration.ipynb** (31 Locations in POC)
- [ ] **02_account_migration.ipynb** (19/20 Accounts in POC)
- [ ] **03_contact_migration.ipynb** (192 Contacts in POC)
- [ ] **04_ban_migration.ipynb** (17/19 BANs in POC)
- [ ] **05_service_migration.ipynb** (17 Services in POC)
- [ ] **06_service_charge_migration.ipynb** (44 Charges in POC with placeholders)
- [ ] **07_offnet_migration.ipynb** (6 Off_Net in POC)

### Post-Migration

- [ ] Review all Excel outputs for errors
- [ ] Validate record counts match expectations
- [ ] Spot-check parent-child relationships in BBF
- [ ] Document any issues for follow-up
- [ ] Archive Excel outputs to permanent storage
- [ ] Update migration tracking spreadsheet
- [ ] **NEW:** Run Service_Charge enrichment to update placeholder values

---

## Additional Resources

| Resource | Location |
|----------|----------|
| Migration Plan | `ES_BBF_MIGRATION_PLAN.md` |
| Progress Log | `MIGRATION_PROGRESS.md` |
| Migration Analysis | `es_bbf_migration_analysis_v5_*.xlsx` |
| Object Tracking | `es_bbf_migration_object_tracking.xlsx` |
| BBF Lookup Relationships | `bbf_lookup_relationships_with_required.xlsx` |
| Field Metadata Scripts | `es_export_sf_fields.py`, `bbf_export_sf_fields.py` |
| Migration Template | `migration_script_template.py` |

---

**Document Version:** 2.1
**Last Synchronized:** 2026-01-23
**Notebooks Reviewed:** 00, 01, 02, 03, 04, 05, 06, 07, 08 (all 8 migration notebooks + 1 export tool)
**Key Update:** All notebooks now implement duplicate prevention via ES_Legacy_ID__c check
**Maintained By:** ES-to-BBF Migration Team

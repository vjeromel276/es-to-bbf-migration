# Migration Filtering Guardrails

Quick reference for data filtering logic across all ES-to-BBF migration notebooks.

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

## Central Policy Reminder

Only migrate data connected to **actively billing Orders** that meet ALL criteria:

| Filter | Criteria |
|--------|----------|
| Status | `IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')` |
| Project Group | `NOT LIKE '%PA MARKET DECOM%'` (exclude decommissioned markets) |
| Record Type | `Service_Order_Record_Type__c = 'Service Order Agreement'` |
| OSS State | `order_state_cd IN ('CL', 'OA')` (Closed, Open Active) |
| Billing Status | `bill_start_date <= TODAY AND (bill_end_date IS NULL OR bill_end_date > TODAY)` |
| BAN Flag | `Billing_Invoice__r.BBF_Ban__c = true` |

**NO ORPHAN DATA** - If it's not connected to a qualifying Order, it doesn't migrate.

## Filtering by Notebook

### 01_location_migration.ipynb

**Purpose:** Migrate ES Address__c → BBF Location__c

**SOQL Filter:**
```sql
SELECT Id, Address_A__c, Address_Z__c
FROM Order
WHERE Billing_Invoice__r.BBF_Ban__c = true
  AND (Address_A__c != null OR Address_Z__c != null)
```

**Logic:**
- Queries Orders with `BBF_Ban__c = true` flag on parent BAN
- Extracts unique Address_A__c and Address_Z__c IDs
- Queries Address__c records for those IDs
- Deduplicates addresses (same address may be used by multiple Orders)

**Parent Dependencies:** None (Location is standalone)

**Skip Conditions:**
- Address already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Address record not found → SKIPPED (logged as error)

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/location_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 02_account_migration.ipynb

**Purpose:** Migrate ES Account → BBF Account

**SOQL Filter:**
```sql
SELECT Id, Name, Account__c
FROM Billing_Invoice__c
WHERE BBF_Ban__c = true
  AND Account__c != null
```

**Logic:**
- Queries BANs with `BBF_Ban__c = true` flag
- Extracts unique Account__c IDs
- Queries Account records for those IDs
- Deduplicates accounts (same account may have multiple BANs)

**Parent Dependencies:** None (Account is root object)

**Skip Conditions:**
- Account already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Duplicate Account detected by BBF → FAILED (logged with error)

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/account_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 03_contact_migration.ipynb

**Purpose:** Migrate ES Contact → BBF Contact

**SOQL Filter:**
```sql
SELECT Id, FirstName, LastName, Email, Phone, AccountId
FROM Contact
WHERE AccountId IN (
  SELECT Id FROM Account
  WHERE BBF_New_Id__c != null
    AND BBF_New_Id__c != ''
)
```

**Logic:**
- Queries ONLY Contacts whose parent Account was successfully migrated
- Account must have `BBF_New_Id__c` populated (proof of migration)
- Maps to migrated Account ID in BBF

**Parent Dependencies:**
- **REQUIRED:** Account must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Account not migrated (`BBF_New_Id__c = null`) → NEVER QUERIED (implicit skip)
- Contact already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing required field (LastName) → FAILED

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/contact_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 04_ban_migration.ipynb

**Purpose:** Migrate ES Billing_Invoice__c → BBF BAN__c

**SOQL Filter:**
```sql
SELECT Id, Name, Account__c, InvoiceNumber__c
FROM Billing_Invoice__c
WHERE BBF_Ban__c = true
  AND Account__r.BBF_New_Id__c != null
  AND Account__r.BBF_New_Id__c != ''
```

**Logic:**
- Queries BANs with `BBF_Ban__c = true` flag
- ONLY includes BANs whose parent Account was successfully migrated
- Maps to migrated Account ID in BBF
- Sets `busUnit__c = 'EVS'` for EverStream

**Parent Dependencies:**
- **REQUIRED:** Account must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Account not migrated (`BBF_New_Id__c = null`) → NEVER QUERIED (implicit skip)
- BAN already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing Account__c lookup → FAILED

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/ban_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 05_service_migration.ipynb

**Purpose:** Migrate ES Order → BBF Service__c

**SOQL Filter (Initial Query):**
```sql
SELECT Id, Billing_Invoice__r.BBF_New_Id__c
FROM Order
WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
  AND (Project_Group__c = null OR (NOT Project_Group__c LIKE '%PA MARKET DECOM%'))
  AND Service_Order_Record_Type__c = 'Service Order Agreement'
  AND Billing_Invoice__r.BBF_New_Id__c != null
  AND Billing_Invoice__r.BBF_New_Id__c != ''
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Day 1 Migration - REQUIRED FIELDS ONLY:**
```python
bbf_service = {
    "Billing_Account_Number__c": bbf_ban_id,        # Master-Detail to BAN__c (REQUIRED)
    "ES_Legacy_ID__c": es_order["Id"]               # Tracking field
}
```

**Account Population (Post-Insert Step):**
After Services are inserted and ES is updated with BBF IDs, a separate step populates Account__c:
```sql
SELECT Id, Billing_Account_Number__c, Billing_Account_Number__r.Account__c, Account__c
FROM Service__c
WHERE ES_Legacy_ID__c != null AND Account__c = null
```

Then updates each Service:
```python
{
    "Id": service_id,
    "Account__c": ban_account_id  # Derived from BAN.Account__c
}
```

**Logic:**
- Queries Orders with full migration criteria (Active + NOT PA MARKET DECOM)
- REQUIRES parent BAN successfully migrated (Master-Detail relationship - BLOCKING)
- **Day 1 Approach:** Only migrate required fields (Master-Detail, Tracking)
- **Account Population:** Separate update step pulls Account from BAN relationship after insert
- **Boolean fields default to False** - no need to set explicitly
- **Name field is AUTONUMBER** - BBF generates automatically, don't set on insert
- **OwnerId not present** - Service__c object doesn't have OwnerId field
- **Enrichment Pass (Day 2+):** Add optional fields like Status, Circuit_ID, MRC, NRC, Bandwidth, etc.

**Process Flow:**
1. Insert Services with Billing_Account_Number__c (master-detail) + ES_Legacy_ID__c
2. Update ES Orders with BBF_New_Id__c
3. **NEW STEP:** Query Services with BAN relationship, update Account__c from BAN.Account__c
4. Result: Services have proper Account relationship populated automatically

**Parent Dependencies:**
- **REQUIRED (Master-Detail):** BAN must have `BBF_New_Id__c`
- **REQUIRED (Filter):** Account must have `BBF_New_Id__c`
- **REQUIRED (Filter):** Address_A must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent BAN not migrated → NEVER QUERIED (implicit skip)
- Parent Account not migrated → NEVER QUERIED (implicit skip)
- Parent Location A not migrated → NEVER QUERIED (implicit skip)
- Service already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing Master-Detail BAN__c → FAILED (Salesforce blocks insert)

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/service_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 06_service_charge_migration.ipynb

**Purpose:** Migrate ES OrderItem → BBF Service_Charge__c

**SOQL Filter:**
```sql
SELECT Id, OrderId, Order.BBF_New_Id__c, Order.Name, Order.Status,
       Product2Id, Product2.Name, Product2.ProductCode,
       Charge_Type__c, MRC__c, NRC__c
FROM OrderItem
WHERE Order.BBF_New_Id__c != null
  AND Order.BBF_New_Id__c != ''
  AND Order.Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
  AND (Order.Project_Group__c = null OR Order.Project_Group__c NOT LIKE '%PA MARKET DECOM%')
  AND Order.Service_Order_Record_Type__c = 'Service Order Agreement'
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Day 1 Migration - REQUIRED FIELDS ONLY:**
```python
bbf_service_charge = {
    "Name": charge_name[:80],                       # From Product2.Name
    "Service__c": bbf_service_id,                   # Master-Detail to Service__c (REQUIRED)
    "Product_Simple__c": product_simple,            # Mapped picklist (REQUIRED)
    "Service_Type_Charge__c": service_type_charge,  # Mapped picklist (REQUIRED) - "MRC" or "NRC"
    "ES_Legacy_ID__c": es_orderitem["Id"]           # Tracking field
}
```

**Picklist Mapping Logic:**
- **Product_Simple__c:** Maps ES Product2 → BBF picklist
  - "Ethernet", "Dark Fiber", "Wavelength", "Internet", "Colocation", "Cloud", "Managed Services", "Other"
- **Service_Type_Charge__c:** Maps ES Charge_Type__c/MRC/NRC → BBF picklist
  - "MRC" (Monthly Recurring), "NRC" (Non-Recurring/One-Time), "Usage"

**Logic:**
- Queries ONLY OrderItems whose parent Order was successfully migrated
- Order must have `BBF_New_Id__c` populated (proof of Service migration)
- **Day 1 Approach:** Only migrate required fields (Name, Master-Detail, two required picklists, Tracking)
- **Boolean fields default to False** - no need to set explicitly (11 boolean fields omitted)
- **Enrichment Pass (Day 2+):** Add optional fields like Description, Amount, Unit_Rate, Start_Date, etc.

**Parent Dependencies:**
- **REQUIRED (Master-Detail):** Service (Order) must have `BBF_New_Id__c`

**Skip Conditions:**
- Parent Service not migrated (`BBF_New_Id__c = null`) → NEVER QUERIED (implicit skip)
- Charge already migrated (`BBF_New_Id__c != null`) → SKIPPED
- Missing Master-Detail Service__c → FAILED (Salesforce blocks insert)
- Invalid Product_Simple__c picklist value → FAILED

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/service_charge_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

### 07_offnet_migration.ipynb

**Purpose:** Migrate ES Off_Net__c → BBF Off_Net__c

**SOQL Filter:**
```sql
SELECT Id, Name, Implementation__c, Implementation__r.BBF_New_Id__c,
       Circuit_Service_Id__c, Location_1__c, Location_1__r.BBF_New_Id__c
FROM Off_Net__c
WHERE Implementation__r.BBF_New_Id__c != null
  AND Implementation__r.BBF_New_Id__c != ''
  AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

**Day 1 Migration - REQUIRED FIELDS ONLY:**
```python
bbf_offnet = {
    "Name": offnet_name[:80],                       # From Circuit_Service_Id__c/Name
    "OwnerId": OWNER_ID,                            # Owner (REQUIRED)
    "ES_Legacy_ID__c": es_offnet["Id"],             # Tracking field
    "Service__c": bbf_service_id                    # Lookup to Service__c (OPTIONAL but included if available)
}
```

**Logic:**
- Queries ONLY Off_Net__c records whose parent Order (Implementation__c) was successfully migrated
- Order must have `BBF_New_Id__c` populated (proof of Service migration)
- **Day 1 Approach:** Only migrate required fields (Name, OwnerId, Tracking)
- **Service__c lookup** is optional in BBF but included if available
- **All other fields omitted for Day 1** - no location lookups, no cost fields, no circuit details
- **Enrichment Pass (Day 2+):** Add Location lookups, cost fields (COGS_MRC__c, COGS_NRC__c), circuit identifiers, vendor details, dates, etc.

**Parent Dependencies:**
- **REQUIRED (Filter):** Service (Implementation) must have `BBF_New_Id__c`
- **OPTIONAL:** Service__c lookup (included if parent Order has BBF_New_Id__c)

**Skip Conditions:**
- Parent Service not migrated (`BBF_New_Id__c = null`) → NEVER QUERIED (implicit skip)
- Off_Net already migrated (`BBF_New_Id__c != null`) → SKIPPED

**Excel Output:** `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/offnet_migration_results_YYYYMMDD_HHMMSS.xlsx`

---

## Cascade Effect Diagram

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

### Scenario 3: Location A Migration Fails

```
Account: ✅ Migrated
BAN: ✅ Migrated
Location A: ❌ FAILED (no BBF_New_Id__c)
    └── Service: ⏭️ SKIPPED (never queried - requires Location A)
        ├── Service_Charge: ⏭️ SKIPPED (never queried)
        └── Off_Net: ⏭️ SKIPPED (never queried)
```

**Impact:** Customer and BAN migrated, but Services requiring that Location blocked

**Mitigation:** Fix Location issue and re-run from 01_location_migration forward, then 05_service_migration

---

### Scenario 4: Service Migration Fails

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
| `Implementation__c` | Off_Net__c | Lookup | Links Off-Net to Service (Order) |

### BBF Org Fields (Target)

| Field | Object | Type | Purpose |
|-------|--------|------|---------|
| `ES_Legacy_ID__c` | All objects | Text(18) | Stores original ES SFID for tracking and deduplication |
| `Billing_Account_Number__c` | Service__c | Master-Detail | **REQUIRED** - Links Service to BAN |
| `Service__c` | Service_Charge__c | Master-Detail | **REQUIRED** - Links Charge to Service |
| `Service__c` | Off_Net__c | Lookup | **REQUIRED** - Links Off-Net to Service |
| `busUnit__c` | BAN__c | Picklist | Set to 'EVS' for all EverStream BANs |

---

## Excel Output Reference

All notebooks output Excel files with standardized structure:

### File Naming Convention

```
/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/results/
    {object}_migration_results_{YYYYMMDD}_{HHMMSS}.xlsx
```

### Standard Sheets

| Sheet | Purpose | Color Coding |
|-------|---------|--------------|
| **Migration Results** | Line-by-line status of all records | 🟢 Green = Success<br>🔴 Red = Failed<br>🟡 Yellow = Skipped |
| **Summary** | Metrics and counts | Counts, percentages, timing |
| **ID Mapping** | Successful mappings only | ES ID → BBF ID pairs |
| **Failed Inserts** | All failures and skipped records | Includes error messages and skip reasons |

### Key Columns in Migration Results Sheet

| Column | Description |
|--------|-------------|
| `ES_ID` | Original ES Salesforce ID (18-char) |
| `BBF_ID` | New BBF Salesforce ID (18-char) - blank if failed/skipped |
| `Status` | Success / Failed / Skipped |
| `Error_Message` | Salesforce error or skip reason |
| `Skip_Reason_*` | Specific parent dependency that failed (Service migration only) |
| Object-specific fields | Name, key identifiers for manual review |

### Summary Sheet Metrics

- Total Records Queried
- Total Successful
- Total Failed
- Total Skipped (already migrated)
- Total Skipped (missing parent)
- Success Rate %
- Execution Time
- Timestamp

---

## Testing Strategy

### UAT Sandbox Testing

**Prep Notebook Controls:**
- `MAX_ORDERS_PER_BAN = 2` → Limits Service/Charge volume per customer
- `TEST_MODE = False` → Required for full-scale UAT (limits removed)

**ES UAT Credentials:**
- Instance: `https://everstream--uat.sandbox.my.salesforce.com`
- Username: stored in `.env` as `ES_UAT_USERNAME`
- Password: stored in `.env` as `ES_UAT_PASSWORD`
- Security Token: stored in `.env` as `ES_UAT_SECURITY_TOKEN`

**BBF Sandbox Credentials:**
- Instance: `https://test.salesforce.com` (sandbox domain)
- Username: stored in `.env` as `BBF_SANDBOX_USERNAME`
- Password: stored in `.env` as `BBF_SANDBOX_PASSWORD`
- Security Token: stored in `.env` as `BBF_SANDBOX_SECURITY_TOKEN`

### Production Execution

**When to Run:**
- After sale closes (Day 1)
- All notebooks tested successfully in sandbox
- Excel outputs reviewed and approved

**Credentials:**
- ES Production: `https://everstream.my.salesforce.com`
- BBF Production: (production domain)
- Stored separately in `.env` (never commit to git)

---

## Troubleshooting Guide

### Issue: High Skip Rate in Contact Migration

**Symptom:** Contact notebook shows many skipped records

**Root Cause:** Parent Accounts not migrated (missing `BBF_New_Id__c`)

**Resolution:**
1. Review Account migration Excel output
2. Identify failed Accounts
3. Fix Account issues (duplicates, missing fields)
4. Re-run 02_account_migration.ipynb
5. Re-run 03_contact_migration.ipynb

---

### Issue: Service Migration Shows Zero Records

**Symptom:** Service notebook queries 0 Orders

**Root Cause:** One or more parent dependencies not met:
- BANs not migrated (`Billing_Invoice__r.BBF_New_Id__c = null`)
- Accounts not migrated (`Account__r.BBF_New_Id__c = null`)
- Locations not migrated (`Address_A__r.BBF_New_Id__c = null`)

**Resolution:**
1. Check BAN migration Excel output → Confirm BANs have `BBF_New_Id__c`
2. Check Account migration Excel output → Confirm Accounts have `BBF_New_Id__c`
3. Check Location migration Excel output → Confirm Locations have `BBF_New_Id__c`
4. Re-run any failed parent migrations
5. Re-run 05_service_migration.ipynb

---

### Issue: Master-Detail Insert Failures

**Symptom:** Salesforce error: "Required fields are missing: [Billing_Account_Number__c]"

**Root Cause:** Master-Detail field is null or invalid

**Resolution:**
- Service__c: Verify BAN migration completed and `BBF_New_Id__c` is populated
- Service_Charge__c: Verify Service migration completed and `BBF_New_Id__c` is populated
- Master-Detail relationships CANNOT be null - parent must exist in BBF

---

### Issue: Duplicate Account Detection

**Symptom:** Account migration fails with "duplicate value found: <field_name>"

**Root Cause:** BBF already has Account with same unique field (Name, External ID, etc.)

**Resolution:**
1. Review BBF Account to determine if it's legitimate duplicate
2. Option A: Skip ES Account, manually map to existing BBF Account ID
3. Option B: Modify ES Account unique field to differentiate
4. Document decision in migration notes

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

### Execution Order

- [ ] 00_uat_ban_prep.ipynb (sets `BBF_Ban__c = true`)
- [ ] 01_location_migration.ipynb
- [ ] 02_account_migration.ipynb
- [ ] 03_contact_migration.ipynb
- [ ] 04_ban_migration.ipynb
- [ ] 05_service_migration.ipynb
- [ ] 06_service_charge_migration.ipynb
- [ ] 07_offnet_migration.ipynb

### Post-Migration

- [ ] Review all Excel outputs for errors
- [ ] Validate record counts match expectations
- [ ] Spot-check parent-child relationships in BBF
- [ ] Document any issues for follow-up
- [ ] Archive Excel outputs to permanent storage
- [ ] Update migration tracking spreadsheet

---

## Additional Resources

| Resource | Location |
|----------|----------|
| Migration Analysis | `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/es_bbf_migration_analysis_v5_*.xlsx` |
| Object Tracking | `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/es_bbf_migration_object_tracking.xlsx` |
| BBF Lookup Relationships | `/mnt/c/Users/vjero/Documents/repos/python-repo/python_scripts/ES-to-BBF-migration/bbf_lookup_relationships_with_required.xlsx` |
| Field Metadata Scripts | `es_export_sf_fields.py`, `bbf_export_sf_fields.py` |
| Migration Template | `migration_script_template.py` |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-14
**Maintained By:** ES-to-BBF Migration Team

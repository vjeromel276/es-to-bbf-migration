# ES to BBF Migration - Master Planning Document

**Last Updated:** 2026-01-14
**Branch:** uat-sandbox-testing

---

## Table of Contents
1. [Central Policy](#central-policy)
2. [Complete Migration Flow](#complete-migration-flow)
3. [Notebook Audit](#notebook-audit)
4. [Issues Identified](#issues-identified)
5. [UAT Testing Strategy](#uat-testing-strategy)
6. [Action Items](#action-items)
7. [Object Dependencies](#object-dependencies)

---

## Central Policy

**THE SOURCE OF TRUTH: Orders must meet these criteria to be migrated:**

**Include Orders where:**
- Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')

**Exclude Orders where:**
- Project_Group__c LIKE '%PA MARKET DECOM%'

All other Project_Group__c values (including NULL or any other project) are **included**.

**Constants (from notebooks):**
```python
ACTIVE_STATUSES = ["Activated", "Suspended (Late Payment)", "Disconnect in Progress"]
WD_PROJECT_GROUP = "PA MARKET DECOM"  # The ONLY exclusion criterion for Project_Group__c
```

**Key Principle:** Only Orders that are actively billing AND NOT in the PA MARKET DECOM project should drive the entire migration. Everything else (Accounts, Contacts, Locations, BANs) should be derived FROM this Order subset.

---

## Complete Migration Flow

### PRODUCTION Flow (with OSS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 0: BAN PREP (es_to_bbf_ban_creation_v12.ipynb)                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. Query all billing_invoice__c with active orders                         │
│  2. Classify each BAN's orders:                                             │
│     - WD-only: ALL orders have Project_Group__c LIKE '%PA MARKET DECOM%'    │
│     - BBF-only: NO orders have PA MARKET DECOM                              │
│     - Mixed: SOME orders have PA MARKET DECOM, SOME don't                   │
│  3. For BBF-only and Mixed BANs:                                            │
│     - Create NEW OSS account (account_id becomes 11XXXX range)              │
│     - Create NEW SF billing_invoice__c with:                                │
│       • Name: A{new_account_id}-BBF                                         │
│       • bbf_ban__c = TRUE  ← This marks it for migration                    │
│       • legacy_es_id__c = original BAN SFID                                 │
│  4. WD-only BANs: SKIPPED (no -BBF BAN created)                             │
│                                                                             │
│  OUTPUT: New -BBF BANs in ES SF with bbf_ban__c = true                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: ORDER MOVE (00_order_move_to_bbf_ban.ipynb)                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. Query Orders meeting criteria (Active + NOT PA MARKET DECOM)            │
│  2. Find their current BAN → Look up corresponding -BBF BAN                 │
│  3. Update Order.Billing_Invoice__c → new -BBF BAN SFID                     │
│  4. Update OSS orders.account_id → new OSS account_id                       │
│                                                                             │
│  RESULT: Qualifying Orders now point to -BBF BANs                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: MIGRATION TO BBF SALESFORCE (initial-day notebooks)               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Run in dependency order:                                                   │
│  1. 01_location_migration.ipynb → Address__c to Location__c                 │
│  2. 02_account_migration.ipynb → Account to Account                         │
│  3. 03_contact_migration.ipynb → Contact to Contact                         │
│  4. 04_ban_migration.ipynb → Billing_Invoice__c (bbf_ban__c=true) to BAN__c │
│  5. 05_service_migration.ipynb → Order to Service__c                        │
│  6. 06_service_charge_migration.ipynb → OrderItem to Service_Charge__c      │
│  7. 07_offnet_migration.ipynb → Off_Net__c to Off_Net__c                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Notebook Audit

### Does each notebook enforce the Order-based policy?

| # | Notebook | Enforces Policy? | Current Filter Logic | Status |
|---|----------|-----------------|---------------------|--------|
| - | `es_to_bbf_ban_creation_v12` | ✅ **YES** | Classifies by `project_group__c LIKE '%PA MARKET DECOM%'` | Production prep |
| 0 | `00_uat_ban_prep` | ✅ **YES** | Full Order criteria, marks BANs with `BBF_Ban__c = true` | **NEW** - UAT prep |
| 0 | `00_order_move_to_bbf_ban` | ✅ **YES** | `Status IN (...) AND Project_Group__c NOT LIKE '%PA MARKET DECOM%'` | Correct |
| 1 | `01_location_migration` | ✅ **YES** | `FILTER_BY_BBF_BAN = True` - filters by Orders on BBF BANs | **UPDATED** |
| 2 | `02_account_migration` | ✅ **YES** | `FILTER_BY_BBF_BAN = True` - filters by Accounts on BBF BANs | **UPDATED** |
| 3 | `03_contact_migration` | ✅ **YES** | `Account.BBF_New_Id__c != null` - inherits from Account | Works if Account is filtered |
| 4 | `04_ban_migration` | ✅ **YES** | `BBF_Ban__c = true` | Works via prep notebook |
| 5 | `05_service_migration` | ✅ **YES** | Full Order criteria in query | Correct |
| 6 | `06_service_charge_migration` | ✅ **YES** | Inherits via `Order.` prefix | Correct |
| 7 | `07_offnet_migration` | ✅ **YES** | `Implementation__r.BBF_New_Id__c != null` | Inherits from Service |

### Summary
- **ALL notebooks now enforce the Order-based policy** ✅
- Upstream notebooks (Account, Location) now filter by `BBF_Ban__c = true`
- Contact migration inherits filtering from Account migration
- Downstream notebooks (Service, Charge, Off-Net) already filtered correctly

---

## Issues Identified

### Issue 1: Account Migration Migrates Too Much
**Current:** Migrates ALL `Type = 'Customer'` accounts
**Should:** Only migrate Accounts that are parents of -BBF BANs

```sql
-- CURRENT (WRONG)
WHERE Type = 'Customer' AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')

-- SHOULD BE
WHERE Id IN (
    SELECT Account__c
    FROM Billing_Invoice__c
    WHERE BBF_Ban__c = true
)
AND (BBF_New_Id__c = null OR BBF_New_Id__c = '')
```

### Issue 2: Contact Migration Migrates Too Much
**Current:** Migrates ALL contacts for migrated accounts
**Should:** Only migrate Contacts for Accounts linked to -BBF BANs

```sql
-- CURRENT (follows from Account migration)
WHERE Account.BBF_New_Id__c != null AND Account.BBF_New_Id__c != ''

-- This is technically correct IF Account migration is fixed
-- But currently migrates too many because Account migration is wrong
```

### Issue 3: Location Migration Migrates Too Much
**Current:** Optional filter, defaults to migrating all addresses
**Should:** Only migrate Addresses referenced by qualifying Orders

```sql
-- SHOULD BE
WHERE Id IN (
    SELECT Address_A__c FROM Order
    WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
      AND (Project_Group__c IS NULL OR Project_Group__c NOT LIKE '%PA MARKET DECOM%')
    UNION
    SELECT Address_Z__c FROM Order
    WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
      AND (Project_Group__c IS NULL OR Project_Group__c NOT LIKE '%PA MARKET DECOM%')
)
```

### Issue 4: UAT Testing Cannot Use Production Prep
**Problem:** `es_to_bbf_ban_creation_v12` creates OSS accounts, which requires OSS access
**Impact:** Can't run standard prep process in UAT without OSS
**Solution Needed:** Alternative way to mark BANs for migration in UAT

### Issue 5: Common Customers Exist in Both Orgs
**Problem:** During UAT testing of 20 accounts, 1 Account was blocked by BBF's duplicate detection
**Impact:** Some customers already exist in BOTH the ES org AND the BBF org ("common customers")
**Discovery:** Identified during UAT Account migration testing on 2026-01-14

**Migration Requirements for Common Customers:**
Even when a customer already exists in BBF, we still need to:
1. Create BAN__c records in BBF for their ES billing relationships
2. Migrate their ES Orders as Service__c records to represent current services

**Stakeholder Decision Required:**
- How should we handle these common customer records?
- Options include:
  - Link to existing BBF Account (requires matching logic)
  - Skip Account creation but proceed with BAN/Service migration
  - Manual review queue for human verification
  - Override duplicate rules for migration

**Matching Strategy Needed:**
- What key should be used to identify common customers?
  - EIN/Tax ID
  - Account Name (fuzzy matching?)
  - External ID field
  - Custom matching logic
- How to handle false positives?

---

## UAT Testing Strategy

### The Challenge
- ES UAT exists, but no OSS development environment
- Cannot run `es_to_bbf_ban_creation_v12` (requires OSS)
- Need to test migration flow from ES UAT → BBF Sandbox

### Proposed Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  UAT PREP: Identify and Mark BANs (NEW NOTEBOOK NEEDED)                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. Query ES UAT Orders using same criteria as production:                  │
│     - Status IN ('Activated', 'Suspended (Late Payment)', ...)              │
│     - Project_Group__c NOT LIKE '%PA MARKET DECOM%'                         │
│                                                                             │
│  2. Get unique Billing_Invoice__c IDs from those Orders                     │
│                                                                             │
│  3. Update those Billing_Invoice__c records:                                │
│     - SET BBF_Ban__c = TRUE                                                 │
│                                                                             │
│  4. Optionally limit to N BANs for testing                                  │
│                                                                             │
│  OUTPUT: ES UAT BANs marked with BBF_Ban__c = true                          │
│          (mimics what the production prep process does)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  UAT MIGRATION: Run modified notebooks                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. 02_account_migration.ipynb                                              │
│     → Modified to only migrate Accounts linked to BBF_Ban__c = true BANs    │
│                                                                             │
│  2. 03_contact_migration.ipynb                                              │
│     → Works as-is (follows Account migration)                               │
│                                                                             │
│  3. 01_location_migration.ipynb                                             │
│     → Modified to only migrate Addresses from qualifying Orders             │
│                                                                             │
│  4. 04_ban_migration.ipynb                                                  │
│     → Works as-is (queries BBF_Ban__c = true)                               │
│                                                                             │
│  5. 05, 06, 07 → Work as-is                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Action Items

### Current POC Pipeline Execution - IN PROGRESS

**Running full migration pipeline with 20 BANs (≤5 orders each):**

- [x] **BAN Prep** - COMPLETED
  - Marked 20 BANs with `BBF_Ban__c = true` in ES UAT
  - Limited to BANs with ≤5 orders each for manageable POC scope

- [x] **Account Migration** - COMPLETED (19/20 success)
  - Migrated: 19 accounts successfully created in BBF Sandbox
  - Blocked: 1 account blocked by BBF duplicate detection rule
  - Issue: Common customer exists in both ES and BBF orgs
  - Requires stakeholder decision on handling strategy

- [x] **Location Migration** - COMPLETED
  - Migrated: 31 locations successfully created in BBF Sandbox
  - Fixed variable name error (FILTER_ACTIVE_ORDERS_ONLY → FILTER_BY_BBF_BAN)
  - All addresses from qualifying Orders migrated successfully

- [x] **Contact Migration** - COMPLETED
  - All contacts for migrated accounts successfully created in BBF Sandbox
  - Inherited filtering from migrated Account records

- [x] **BAN Migration** - COMPLETED (with 2 failures)
  - Most BANs migrated successfully
  - Failed: 2 BANs due to Payment Terms field picklist value issues
  - Issue: Payment Terms corrections not applied before migration
  - Resolution needed: Update Payment Terms in ES, then re-run for failed BANs

- [ ] **Service Migration** - IN PROGRESS
  - TEST_MODE = False enabled for POC execution
  - Ready to migrate Order → Service__c

- [ ] **Service Charge Migration** - IN PROGRESS
  - TEST_MODE = False enabled for POC execution
  - Ready to migrate OrderItem → Service_Charge__c

- [ ] **Off-Net Migration** - IN PROGRESS
  - TEST_MODE = False enabled for POC execution
  - Ready to migrate Off_Net__c → Off_Net__c

### Immediate (for UAT Testing) - COMPLETED

- [x] **Create UAT BAN Prep Notebook** (`00_uat_ban_prep.ipynb`) ✅
  - Query Orders with Active + NOT PA MARKET DECOM criteria
  - Get unique BAN IDs from those Orders
  - Set `BBF_Ban__c = TRUE` on those BANs
  - Configuration options:
    - `BAN_LIMIT` - Max BANs to mark (default: 20)
    - `MAX_ORDERS_PER_BAN` - Max orders per BAN (default: 5) - keeps POC small
    - `DRY_RUN` - Preview changes without updating (default: True)
  - Exports Account IDs and Address IDs for reference

- [x] **Modify Account Migration** (`02_account_migration.ipynb`) ✅
  - Added `FILTER_BY_BBF_BAN = True` option (default)
  - Queries BANs with `BBF_Ban__c = true` to get Account IDs
  - Only migrates Accounts linked to those BANs

- [x] **Modify Location Migration** (`01_location_migration.ipynb`) ✅
  - Added `FILTER_BY_BBF_BAN = True` option (default)
  - Queries Orders linked to `BBF_Ban__c = true` BANs
  - Applies full migration criteria (Active + NOT PA MARKET DECOM)
  - Only migrates Addresses from qualifying Orders

### Future (for Production Consistency)

- [ ] **Stakeholder Decision: Common Customer Handling**
  - Need decision on how to handle customers that exist in both ES and BBF orgs
  - Define matching strategy (EIN, Account Name, External ID, etc.)
  - Determine workflow: link to existing, skip, manual review, or override duplicates
  - Even if Account exists, must still create BAN__c and migrate Service__c records

- [ ] **Create Migration Scope Notebook** (`00_migration_scope.ipynb`)
  - Master notebook that identifies ALL IDs to migrate
  - Exports ID lists for other notebooks to consume
  - Single source of truth for the Order criteria

- [ ] **Standardize All Notebooks**
  - All notebooks read from migration scope output
  - Ensures consistent filtering across entire pipeline

---

## Object Dependencies

```
Account (no dependencies)
    ├── Contact (requires Account)
    └── Billing_Invoice__c / BAN__c (requires Account)
            └── Service__c (requires BAN, Account, Location)
                    ├── Service_Charge__c (requires Service)
                    └── Off_Net__c (requires Service, Location)

Location__c / Address__c (no dependencies, but derived from Orders)

Order (the source of truth)
    ├── Billing_Invoice__c (Order.Billing_Invoice__c)
    ├── Account (via Billing_Invoice__c.Account__c)
    ├── Address_A__c (Order.Address_A__c)
    └── Address_Z__c (Order.Address_Z__c)
```

### Migration Order

| Wave | Object | ES Source | BBF Target | Dependencies |
|------|--------|-----------|------------|--------------|
| 0 | Mark BANs | - | - | Identify qualifying Orders |
| 1 | Location | Address__c | Location__c | None |
| 1 | Account | Account | Account | None |
| 2 | Contact | Contact | Contact | Account |
| 3 | BAN | Billing_Invoice__c | BAN__c | Account |
| 4 | Service | Order | Service__c | BAN, Account, Location |
| 5 | Service Charge | OrderItem | Service_Charge__c | Service |
| 5 | Off-Net | Off_Net__c | Off_Net__c | Service, Location |

---

## Quick Reference

### Key Files

| Purpose | File |
|---------|------|
| BAN Prep (Production) | `es_to_bbf_ban_creation_v12.ipynb` |
| Order Move | `initial-day/00_order_move_to_bbf_ban.ipynb` |
| Location Migration | `initial-day/01_location_migration.ipynb` |
| Account Migration | `initial-day/02_account_migration.ipynb` |
| Contact Migration | `initial-day/03_contact_migration.ipynb` |
| BAN Migration | `initial-day/04_ban_migration.ipynb` |
| Service Migration | `initial-day/05_service_migration.ipynb` |
| Service Charge Migration | `initial-day/06_service_charge_migration.ipynb` |
| Off-Net Migration | `initial-day/07_offnet_migration.ipynb` |

### Key Fields

| Field | Object | Purpose |
|-------|--------|---------|
| `BBF_Ban__c` | Billing_Invoice__c | Checkbox to mark BAN for migration |
| `BBF_New_Id__c` | All ES objects | Stores BBF SFID after migration |
| `ES_Legacy_ID__c` | All BBF objects | Stores original ES SFID for tracking |
| `legacy_es_id__c` | Billing_Invoice__c | Links -BBF BAN to original BAN |

### Key Statuses

| Status | Meaning |
|--------|---------|
| `Activated` | Active billing |
| `Suspended (Late Payment)` | Still billing, payment issue |
| `Disconnect in Progress` | Pending disconnect, still billing |
| `PA MARKET DECOM` | WindDown project - DO NOT MIGRATE |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-14 | Initial document created |
| | Documented complete production flow |
| | Identified issues with upstream notebooks |
| | Proposed UAT testing strategy |
| | Created `00_uat_ban_prep.ipynb` - UAT BAN prep notebook |
| | Updated `02_account_migration.ipynb` - Added `FILTER_BY_BBF_BAN` option |
| | Updated `01_location_migration.ipynb` - Added `FILTER_BY_BBF_BAN` option |
| | All notebooks now enforce the Order-based migration policy |
| | Added `MAX_ORDERS_PER_BAN` option to UAT prep (default: 5) for smaller POC scope |
| | UAT Testing: Marked 20 BANs (≤5 orders each) with BBF_Ban__c = true |
| | Set TEST_MODE = False on migration notebooks to migrate all records in scope |
| | **Issue 5 Discovered:** During UAT Account migration testing, 1 of 20 accounts blocked by BBF duplicate detection |
| | Common customers exist in both ES and BBF orgs - requires stakeholder decision on handling |
| | Added action item: Need matching strategy and workflow for common customer accounts |
| | **POC Pipeline Execution Started:** Running full migration pipeline with 20 BANs |
| | Account migration completed: 19/20 accounts migrated successfully, 1 blocked by duplicate detection |
| | **Created migration-docs-sync agent** - For keeping all migration documentation synchronized |
| | **Created MIGRATION_FILTERING_GUARDRAILS.md** - Quick reference for all filtering logic across the pipeline |
| | Location migration completed: 31 locations migrated successfully |
| | Contact migration completed: All contacts for 19 accounts migrated |
| | BAN migration completed: Most BANs successful, 2 failures due to Payment Terms picklist issues |
| | **Updated notebooks 05, 06, 07** - Converted to Day 1 required-fields-only approach |
| | Service__c: Only Billing_Account_Number__c (master-detail) + ES_Legacy_ID__c; Name is autonumber, no OwnerId field |
| | Service_Charge__c: Only Name, Service__c (master-detail), Product_Simple__c, Service_Type_Charge__c, ES_Legacy_ID__c |
| | Off_Net__c: Only Name, OwnerId, ES_Legacy_ID__c, Service__c (optional) |
| | Removed all boolean fields (default to False), corrected field names based on actual BBF metadata |
| | User added ES_Legacy_ID__c field to Service__c, Service_Charge__c, Off_Net__c in BBF org |
| | **Updated 05_service_migration.ipynb** - Added Account population from BAN relationship after Service insert |
| | Service migration now: 1) Insert Services, 2) Update ES, 3) Populate Account__c from BAN.Account__c automatically |

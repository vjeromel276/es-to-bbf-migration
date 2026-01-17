# ES to BBF Migration Pipeline - Complete User Guide

A comprehensive guide for running the ES (EverStream) to BBF (BlueBird Fiber) Salesforce data migration **from scratch**.

**Last Updated:** 2026-01-17

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Day One Migration](#phase-1-day-one-migration)
4. [Phase 2: Day Two Setup (Creating Mappings)](#phase-2-day-two-setup-creating-mappings)
5. [Phase 3: Day Two Business Review](#phase-3-day-two-business-review)
6. [Phase 4: Day Two Enrichment Execution](#phase-4-day-two-enrichment-execution)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)
9. [Complete Checklist](#complete-checklist)

---

## Overview

This migration pipeline transfers data from EverStream (ES) to BlueBird Fiber (BBF) Salesforce orgs in phases:

| Phase | Purpose | Time Estimate |
|-------|---------|---------------|
| **Phase 1: Day One** | Create foundation records with required fields | 2-4 hours |
| **Phase 2: Day Two Setup** | Export metadata, create mappings, generate transformers | 4-8 hours |
| **Phase 3: Day Two Review** | Business stakeholders review picklist mappings | 1-5 days |
| **Phase 4: Day Two Enrichment** | Update transformers and run enrichment | 2-4 hours |

### Objects Migrated

| ES Object | BBF Object | Day 1 Fields | Day 2 Transformers |
|-----------|------------|--------------|-------------------|
| Address__c | Location__c | Required only | 16 functions |
| Account | Account | Required only | 4 functions |
| Contact | Contact | Required only | 1 function |
| Billing_Invoice__c | BAN__c | Required only | 3 functions |
| Order | Service__c | Required only | 26 functions |
| OrderItem | Service_Charge__c | Required only | 19 functions |
| Off_Net__c | Off_Net__c | Required only | 12 functions |

---

## Prerequisites

### Required Software

```bash
# Check Python version (3.10+ required)
python --version

# Install all required packages
pip install simple-salesforce pandas openpyxl psycopg2-binary
```

### Required Access

| System | Purpose | Access Needed |
|--------|---------|---------------|
| ES Salesforce | Source data | Read/Write on migration objects |
| BBF Salesforce | Target data | Create/Update on target objects |
| Heroku Database | Production only | Read access |
| OSS Database | Production only | Read/Write access |

### Directory Structure

```
es-to-bbf-migration/
├── initial-day/                    # Day One migration notebooks
│   ├── 00_uat_ban_prep.ipynb
│   ├── 00_order_move_to_bbf_ban.ipynb
│   ├── 01_location_migration.ipynb
│   ├── 02_account_migration.ipynb
│   ├── 03_contact_migration.ipynb
│   ├── 04_ban_migration.ipynb
│   ├── 05_service_migration.ipynb
│   ├── 06_service_charge_migration.ipynb
│   └── 07_offnet_migration.ipynb
├── day-two/                        # Day Two enrichment
│   ├── exports/                    # Field metadata CSV exports
│   ├── mappings/                   # Field mapping Excel files
│   ├── transformers/               # Generated Python modules
│   └── tools/                      # Scripts for generating mappings
└── *.md                            # Documentation files
```

---

## Phase 1: Day One Migration

### Execution Flow

```
STEP 0: Prep Notebook (choose one)
        ├── UAT:  00_uat_ban_prep.ipynb
        └── PROD: 00_order_move_to_bbf_ban.ipynb
                    │
                    ▼
STEP 1: 01_location_migration.ipynb
STEP 2: 02_account_migration.ipynb
STEP 3: 03_contact_migration.ipynb (depends on Step 2)
STEP 4: 04_ban_migration.ipynb (depends on Step 2)
STEP 5: 05_service_migration.ipynb (depends on Steps 1, 4)
STEP 6: 06_service_charge_migration.ipynb (depends on Step 5)
STEP 7: 07_offnet_migration.ipynb (depends on Steps 1, 5)
```

---

### Step 0A: UAT BAN Prep (`00_uat_ban_prep.ipynb`)

**When:** UAT testing without OSS database access

**What It Does:** Marks ES BANs with `BBF_Ban__c = true` to flag for migration

1. Open notebook in Jupyter/VS Code
2. Configure Cell 2:
   ```python
   ES_USERNAME = "your-username@everstream.net.uat"
   ES_PASSWORD = "your-password"
   ES_TOKEN = "your-security-token"
   ES_DOMAIN = "test"

   DRY_RUN = True          # Preview first
   BAN_LIMIT = 20          # Max BANs to mark
   MAX_ORDERS_PER_BAN = 5  # Filter to small BANs
   ```
3. Run All Cells with `DRY_RUN = True`
4. Review output Excel
5. Set `DRY_RUN = False` and re-run

**Output:** `uat_ban_prep_live_run_*.xlsx`

---

### Step 0B: Production Order Move (`00_order_move_to_bbf_ban.ipynb`)

**When:** Production after BAN creation (v8/v12) has run

**What It Does:** Moves orders to -BBF BANs in Salesforce AND OSS

1. Open notebook
2. Configure Cell 2:
   ```python
   ES_USERNAME = "sfdcapi@everstream.net"
   ES_PASSWORD = "your-password"
   ES_TOKEN = "your-security-token"

   DRY_RUN = True  # Preview first
   ```
3. Run All Cells with `DRY_RUN = True`
4. Review Excel sheets
5. Set `DRY_RUN = False` and re-run

**Output:** `es_order_move_to_bbf_ban_*.xlsx`

---

### Steps 1-7: Migration Notebooks

**Standard Configuration (Cell 2):**
```python
# ES (Source)
ES_USERNAME = "your-username@everstream.net.uat"
ES_PASSWORD = "your-password"
ES_TOKEN = "your-security-token"
ES_DOMAIN = "test"  # "login" for production

# BBF (Target)
BBF_USERNAME = "your-username@company.net"
BBF_PASSWORD = "your-password"
BBF_TOKEN = "your-security-token"
BBF_DOMAIN = "test"  # "login" for production

# Options
TEST_MODE = False
OWNER_ID = "005Ea00000ZOGFZIA5"
DEFAULT_BUS_UNIT = "EVS"
```

**For Each Notebook (Steps 1-7):**
1. Open notebook
2. Configure credentials in Cell 2
3. Run All Cells
4. Review output for errors
5. Check Excel output
6. Proceed to next notebook

**Verification:**
```sql
-- Run in BBF after all notebooks complete
SELECT COUNT() FROM Location__c WHERE ES_Legacy_ID__c != null
SELECT COUNT() FROM Account WHERE ES_Legacy_ID__c != null
SELECT COUNT() FROM BAN__c WHERE ES_Legacy_ID__c != null
SELECT COUNT() FROM Service__c WHERE ES_Legacy_ID__c != null
```

---

## Phase 2: Day Two Setup (Creating Mappings)

This phase creates the field mappings and transformer functions needed for enrichment.

### Execution Flow

```
STEP D2-S1: Export ES Field Metadata (7 objects)
                    │
                    ▼
STEP D2-S2: Export BBF Field Metadata (7 objects)
                    │
                    ▼
STEP D2-S3: Create Mapping Excel Files (7 files)
                    │
                    ▼
STEP D2-S4: Generate Transformer Functions (7 modules)
                    │
                    ▼
            Ready for Business Review (Phase 3)
```

---

### Step D2-S1: Export ES Field Metadata

Export field definitions from ES Salesforce for all migration objects.

**Location:** `day-two/tools/`

**Script:** `es_export_sf_fields_with_picklists.py`

**First, update credentials in the script (lines 10-13):**
```python
sf_username = "sfdcapi@everstream.net"
sf_password = "your-password"
sf_token = "your-security-token"
sf_domain = "login"  # or "test" for sandbox
```

**Run for each object:**
```bash
cd /home/vjl2dev/projects/salesforce/es-to-bbf-migration

# Export ES Address__c fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Address__c \
  --output-dir day-two/exports

# Export ES Account fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Account \
  --output-dir day-two/exports

# Export ES Contact fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Contact \
  --output-dir day-two/exports

# Export ES Billing_Invoice__c fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Billing_Invoice__c \
  --output-dir day-two/exports

# Export ES Order fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Order \
  --output-dir day-two/exports

# Export ES OrderItem fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object OrderItem \
  --output-dir day-two/exports

# Export ES Off_Net__c fields
python day-two/tools/es_export_sf_fields_with_picklists.py \
  --object Off_Net__c \
  --output-dir day-two/exports
```

**Output Files Created:**
```
day-two/exports/
├── es_Address__c_fields_with_picklists.csv
├── es_Account_fields_with_picklists.csv
├── es_Contact_fields_with_picklists.csv
├── es_Billing_Invoice__c_fields_with_picklists.csv
├── es_Order_fields_with_picklists.csv
├── es_OrderItem_fields_with_picklists.csv
└── es_Off_Net__c_fields_with_picklists.csv
```

---

### Step D2-S2: Export BBF Field Metadata

Export field definitions from BBF Salesforce for all target objects.

**Script:** `bbf_export_sf_fields_with_picklists.py`

**First, update credentials in the script:**
```python
sf_username = "your-username@company.net"
sf_password = "your-password"
sf_token = "your-security-token"
sf_domain = "test"  # or "login" for production
```

**Run for each object:**
```bash
# Export BBF Location__c fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Location__c \
  --output-dir day-two/exports

# Export BBF Account fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Account \
  --output-dir day-two/exports

# Export BBF Contact fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Contact \
  --output-dir day-two/exports

# Export BBF BAN__c fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object BAN__c \
  --output-dir day-two/exports

# Export BBF Service__c fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Service__c \
  --output-dir day-two/exports

# Export BBF Service_Charge__c fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Service_Charge__c \
  --output-dir day-two/exports

# Export BBF Off_Net__c fields
python day-two/tools/bbf_export_sf_fields_with_picklists.py \
  --object Off_Net__c \
  --output-dir day-two/exports
```

**Output Files Created:**
```
day-two/exports/
├── bbf_Location__c_fields_with_picklists.csv
├── bbf_Account_fields_with_picklists.csv
├── bbf_Contact_fields_with_picklists.csv
├── bbf_BAN__c_fields_with_picklists.csv
├── bbf_Service__c_fields_with_picklists.csv
├── bbf_Service_Charge__c_fields_with_picklists.csv
└── bbf_Off_Net__c_fields_with_picklists.csv
```

---

### Step D2-S3: Create Mapping Excel Files

Create field mapping documents using semantic AI matching.

**Scripts Location:** `day-two/tools/`

**Run each mapping script:**
```bash
cd /home/vjl2dev/projects/salesforce/es-to-bbf-migration

# Create Location mapping (Address__c → Location__c)
python day-two/tools/create_address_location_mapping.py

# Create Account mapping
python day-two/tools/create_account_mapping.py

# Create Contact mapping
python day-two/tools/create_contact_mapping.py

# Create BAN mapping (Billing_Invoice__c → BAN__c)
python day-two/tools/create_billing_invoice_to_ban_mapping.py

# Create Service mapping (Order → Service__c)
# Note: This may be embedded in another script or need manual creation

# Create Service Charge mapping (OrderItem → Service_Charge__c)
python day-two/tools/create_orderitem_servicecharge_mapping.py

# Create Off_Net mapping
python day-two/tools/generate_off_net_mapping_semantic.py
```

**Output Files Created:**
```
day-two/mappings/
├── ES_Address__c_to_BBF_Location__c_mapping.xlsx
├── ES_Account_to_BBF_Account_mapping.xlsx
├── ES_Contact_to_BBF_Contact_mapping.xlsx
├── ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx
├── ES_Order_to_BBF_Service__c_mapping.xlsx
├── ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx
└── ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx
```

**Each Excel File Contains:**
- **Sheet 1: Field_Mapping** - BBF fields mapped to ES fields with confidence levels
- **Sheet 2: Picklist_Mapping** - Picklist value translations

---

### Step D2-S4: Generate Transformer Functions

Generate Python transformer modules from the mapping Excel files.

**Script:** `day-two/tools/generate_transformers.py`

**Generate all transformers:**
```bash
cd /home/vjl2dev/projects/salesforce/es-to-bbf-migration

# Generate all transformers at once
python day-two/tools/generate_transformers.py --all

# Or generate individually:
python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx \
  --output day-two/transformers/account_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Address__c_to_BBF_Location__c_mapping.xlsx \
  --output day-two/transformers/location_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Contact_to_BBF_Contact_mapping.xlsx \
  --output day-two/transformers/contact_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx \
  --output day-two/transformers/ban_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Order_to_BBF_Service__c_mapping.xlsx \
  --output day-two/transformers/service_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx \
  --output day-two/transformers/service_charge_transformers.py

python day-two/tools/generate_transformers.py \
  --mapping day-two/mappings/ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx \
  --output day-two/transformers/off_net_transformers.py
```

**Output Files Created:**
```
day-two/transformers/
├── __init__.py
├── account_transformers.py
├── location_transformers.py
├── contact_transformers.py
├── ban_transformers.py
├── service_transformers.py
├── service_charge_transformers.py
└── off_net_transformers.py
```

**Verify Generation:**
```bash
# Check that files were created
ls -la day-two/transformers/

# Check line counts
wc -l day-two/transformers/*.py
```

---

## Phase 3: Day Two Business Review

Business stakeholders must review the mapping Excel files and make decisions on picklist values.

### What Needs Review

Each mapping Excel file has a **Picklist_Mapping** sheet with rows that need business decisions.

**Files to Review:**

| File | Location | Values Needing Decision |
|------|----------|-------------------------|
| `ES_Account_to_BBF_Account_mapping.xlsx` | `day-two/mappings/` | ~66 values |
| `ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx` | `day-two/mappings/` | ~54 values |
| `ES_Contact_to_BBF_Contact_mapping.xlsx` | `day-two/mappings/` | ~43 values |
| `ES_Order_to_BBF_Service__c_mapping.xlsx` | `day-two/mappings/` | ~23 values |
| `ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx` | `day-two/mappings/` | ~6 values |
| `ES_Address__c_to_BBF_Location__c_mapping.xlsx` | `day-two/mappings/` | ~2 values |
| `ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx` | `day-two/mappings/` | ~1 value |

---

### How to Review Each Excel File

**Step 1:** Open the Excel file

**Step 2:** Go to **"Picklist_Mapping"** sheet

**Step 3:** Understand the columns:
- **Column A: ES_Field** - ES source field name
- **Column B: ES_Picklist_Value** - The ES value that needs mapping
- **Column C: BBF_Field** - BBF target field name
- **Column D: Suggested_Mapping** - Either exact match OR list of valid BBF values
- **Column E: Notes** - Match status
- **Column F: BBF_Final_Value** - **YOU FILL THIS IN**

**Step 4:** For each row:

| Row Color | Notes Value | Action |
|-----------|-------------|--------|
| Green | "Exact Match" | No action needed - mapping is automatic |
| Yellow | "Close Match" | Validate the suggested mapping is correct |
| Red | "No Match - Select from list" | **Select appropriate BBF value from Column D** |

**Step 5:** For red rows, copy the appropriate value from Column D into Column F

**Example:**
```
A: Invoice_Delivery_Preference__c
B: E-mail
C: invType__c
D: Email | Print | Both
E: No Match - Select from list
F: [Enter: Email]    <-- You fill this in
```

**Step 6:** Save the Excel file

---

### After Business Review

Once all mapping files are reviewed and Column F is filled in:

1. Update the transformer picklist maps (see Phase 4)
2. Test the transformers
3. Run enrichment notebooks

---

## Phase 4: Day Two Enrichment Execution

After business review is complete, update transformers and run enrichment.

### Execution Flow

```
STEP D2-E1: Update Transformer Picklist Maps
                    │
                    ▼
STEP D2-E2: Test Transformers
                    │
                    ▼
STEP D2-E3: Create Enrichment Notebooks
                    │
                    ▼
STEP D2-E4: Run Enrichment (in order)
            ├── 01_location_enrichment.ipynb
            ├── 02_account_enrichment.ipynb
            ├── 03_contact_enrichment.ipynb
            ├── 04_ban_enrichment.ipynb
            ├── 05_service_enrichment.ipynb
            ├── 06_service_charge_enrichment.ipynb
            └── 07_offnet_enrichment.ipynb
                    │
                    ▼
STEP D2-E5: Verify Enrichment
```

---

### Step D2-E1: Update Transformer Picklist Maps

Add the business decisions to the transformer Python files.

**Example:** Update `day-two/transformers/account_transformers.py`

Find the picklist map at the top of the file:
```python
INDUSTRY_MAP = {
    'Accommodation': 'Accommodation',
    'Administrative': 'Administrative',
    # ... existing mappings ...

    # ADD NEW MAPPINGS FROM BUSINESS REVIEW:
    'Carrier': 'Telecommunications',        # From Excel review
    'CLEC/ILEC': 'Telecommunications',      # From Excel review
    'Internet Provider': 'Technology',      # From Excel review
}
```

Repeat for each transformer file with picklist values.

---

### Step D2-E2: Test Transformers

Create a test script to verify transformers work:

```python
# test_transformers.py
import sys
sys.path.insert(0, '/home/vjl2dev/projects/salesforce/es-to-bbf-migration')

from day_two.transformers.account_transformers import TRANSFORMERS, apply_transformers

# Test with sample data
sample_es_record = {
    'Legally_Organized_Under__c': 'Michigan',
    'Sales_Tax_Exemption__c': True,
    'OneCommunity_Entity__c': 'EverStream',
    'Company_Legal_Name__c': 'Test Company LLC'
}

print("Testing apply_transformers:")
result = apply_transformers(sample_es_record)
for field, value in result.items():
    print(f"  {field}: {value}")
```

**Run:**
```bash
cd /home/vjl2dev/projects/salesforce/es-to-bbf-migration
python test_transformers.py
```

---

### Step D2-E3: Create Enrichment Notebooks

Create 7 enrichment notebooks in `initial-day/` directory.

**Enrichment Notebook Template:**

```python
# Cell 1: Setup
import sys
import pandas as pd
from simple_salesforce import Salesforce
from datetime import datetime
from openpyxl import Workbook

sys.path.insert(0, '/home/vjl2dev/projects/salesforce/es-to-bbf-migration')
from day_two.transformers.account_transformers import TRANSFORMERS, apply_transformers, FIELD_MAPPING

print(f"Transformers: {list(TRANSFORMERS.keys())}")

# Cell 2: Configuration
ES_USERNAME = "your-username@everstream.net.uat"
ES_PASSWORD = "your-password"
ES_TOKEN = "your-security-token"
ES_DOMAIN = "test"

BBF_USERNAME = "your-username@company.net"
BBF_PASSWORD = "your-password"
BBF_TOKEN = "your-security-token"
BBF_DOMAIN = "test"

TEST_MODE = True
TEST_LIMIT = 5
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"account_enrichment_{timestamp}.xlsx"

# Cell 3: Connect
es_sf = Salesforce(username=ES_USERNAME, password=ES_PASSWORD,
                   security_token=ES_TOKEN, domain=ES_DOMAIN)
bbf_sf = Salesforce(username=BBF_USERNAME, password=BBF_PASSWORD,
                    security_token=BBF_TOKEN, domain=BBF_DOMAIN)
print(f"Connected to ES: {es_sf.sf_instance}")
print(f"Connected to BBF: {bbf_sf.sf_instance}")

# Cell 4: Query BBF records to enrich
bbf_query = "SELECT Id, ES_Legacy_ID__c, Name FROM Account WHERE ES_Legacy_ID__c != null"
if TEST_MODE:
    bbf_query += f" LIMIT {TEST_LIMIT}"
bbf_records = bbf_sf.query_all(bbf_query)['records']
print(f"Found {len(bbf_records)} BBF records to enrich")

# Cell 5: Query ES source records
es_ids = [r['ES_Legacy_ID__c'] for r in bbf_records if r.get('ES_Legacy_ID__c')]
es_fields = list(set(FIELD_MAPPING.values()))
es_query = f"SELECT Id, {', '.join(es_fields)} FROM Account WHERE Id IN ('" + "','".join(es_ids) + "')"
es_records = es_sf.query_all(es_query)['records']
es_lookup = {r['Id']: r for r in es_records}
print(f"Found {len(es_records)} ES source records")

# Cell 6: Apply transformers
updates = []
errors = []
for bbf_rec in bbf_records:
    es_id = bbf_rec.get('ES_Legacy_ID__c')
    es_rec = es_lookup.get(es_id)
    if not es_rec:
        errors.append({'bbf_id': bbf_rec['Id'], 'error': 'ES record not found'})
        continue
    try:
        enrichment = apply_transformers(es_rec)
        if any(v is not None for v in enrichment.values()):
            enrichment['Id'] = bbf_rec['Id']
            updates.append(enrichment)
    except Exception as e:
        errors.append({'bbf_id': bbf_rec['Id'], 'error': str(e)})

print(f"Prepared {len(updates)} records for enrichment")
print(f"Errors: {len(errors)}")

# Cell 7: Update BBF
if updates:
    results = bbf_sf.bulk.Account.update(updates)
    success = sum(1 for r in results if r.get('success'))
    failed = sum(1 for r in results if not r.get('success'))
    print(f"Updated: {success}, Failed: {failed}")

# Cell 8: Save output
wb = Workbook()
ws1 = wb.active
ws1.title = "Summary"
ws1.append(["Enrichment Summary"])
ws1.append(["Records Found", len(bbf_records)])
ws1.append(["Records Enriched", len(updates)])
ws1.append(["Errors", len(errors)])
wb.save(output_file)
print(f"Output: {output_file}")
```

**Create These 7 Notebooks:**

| Notebook | Transformer Import | BBF Object | ES Object |
|----------|-------------------|------------|-----------|
| `01_location_enrichment.ipynb` | `location_transformers` | `Location__c` | `Address__c` |
| `02_account_enrichment.ipynb` | `account_transformers` | `Account` | `Account` |
| `03_contact_enrichment.ipynb` | `contact_transformers` | `Contact` | `Contact` |
| `04_ban_enrichment.ipynb` | `ban_transformers` | `BAN__c` | `Billing_Invoice__c` |
| `05_service_enrichment.ipynb` | `service_transformers` | `Service__c` | `Order` |
| `06_service_charge_enrichment.ipynb` | `service_charge_transformers` | `Service_Charge__c` | `OrderItem` |
| `07_offnet_enrichment.ipynb` | `off_net_transformers` | `Off_Net__c` | `Off_Net__c` |

---

### Step D2-E4: Run Enrichment Notebooks

Run in numeric order:
1. `01_location_enrichment.ipynb`
2. `02_account_enrichment.ipynb`
3. `03_contact_enrichment.ipynb`
4. `04_ban_enrichment.ipynb`
5. `05_service_enrichment.ipynb`
6. `06_service_charge_enrichment.ipynb`
7. `07_offnet_enrichment.ipynb`

---

### Step D2-E5: Verify Enrichment

Check that enriched fields are populated:
```sql
SELECT Id, Name, Industry, Type, proposalmanager__Primary_State__c
FROM Account
WHERE ES_Legacy_ID__c != null
LIMIT 10
```

---

## Troubleshooting

### Phase 1 Issues

**No BANs with BBF_Ban__c = true**
```
⚠️ No BANs found!
```
Fix: Run Step 0 prep notebook first

**Duplicate Detection**
```
DUPLICATES_DETECTED
```
Fix: Common customer - see `STAKEHOLDER_DECISION_Common_Customer_Handling.md`

**Master-Detail Failed**
```
REQUIRED_FIELD_MISSING: [Billing_Account_Number__c]
```
Fix: Run dependency notebook first (BAN before Service)

### Phase 2 Issues

**Module Not Found**
```
ModuleNotFoundError: No module named 'day_two'
```
Fix: Add path at top of script:
```python
import sys
sys.path.insert(0, '/home/vjl2dev/projects/salesforce/es-to-bbf-migration')
```

**CSV Not Found**
```
FileNotFoundError: es_Account_fields_with_picklists.csv
```
Fix: Run export script first (Step D2-S1 or D2-S2)

**Invalid Picklist Value**
```
INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST
```
Fix: Update the picklist map in the transformer file

---

## Rollback Procedures

### Delete from BBF (reverse order)
```apex
// Run in BBF Developer Console
List<Off_Net__c> offnets = [SELECT Id FROM Off_Net__c WHERE ES_Legacy_ID__c != null];
delete offnets;

List<Service_Charge__c> charges = [SELECT Id FROM Service_Charge__c WHERE ES_Legacy_ID__c != null];
delete charges;

List<Service__c> svcs = [SELECT Id FROM Service__c WHERE ES_Legacy_ID__c != null];
delete svcs;

List<BAN__c> bans = [SELECT Id FROM BAN__c WHERE ES_Legacy_ID__c != null];
delete bans;

List<Contact> cons = [SELECT Id FROM Contact WHERE ES_Legacy_ID__c != null];
delete cons;

List<Account> accts = [SELECT Id FROM Account WHERE ES_Legacy_ID__c != null];
delete accts;

List<Location__c> locs = [SELECT Id FROM Location__c WHERE ES_Legacy_ID__c != null];
delete locs;
```

### Clear ES Tracking
```apex
// Run in ES Developer Console
List<Billing_Invoice__c> bans = [SELECT Id FROM Billing_Invoice__c WHERE BBF_Ban__c = true];
for (Billing_Invoice__c bi : bans) { bi.BBF_Ban__c = false; }
update bans;

// Clear BBF_New_Id__c from each object...
```

---

## Complete Checklist

### Phase 1: Day One Migration
- [ ] Step 0: Run prep notebook (`00_uat_ban_prep` or `00_order_move_to_bbf_ban`)
- [ ] Step 1: Run `01_location_migration.ipynb`
- [ ] Step 2: Run `02_account_migration.ipynb`
- [ ] Step 3: Run `03_contact_migration.ipynb`
- [ ] Step 4: Run `04_ban_migration.ipynb`
- [ ] Step 5: Run `05_service_migration.ipynb`
- [ ] Step 6: Run `06_service_charge_migration.ipynb`
- [ ] Step 7: Run `07_offnet_migration.ipynb`
- [ ] Verify record counts in BBF

### Phase 2: Day Two Setup
- [ ] D2-S1: Export ES field metadata (7 objects)
- [ ] D2-S2: Export BBF field metadata (7 objects)
- [ ] D2-S3: Create mapping Excel files (7 files)
- [ ] D2-S4: Generate transformer functions (7 modules)

### Phase 3: Day Two Business Review
- [ ] Review `ES_Account_to_BBF_Account_mapping.xlsx`
- [ ] Review `ES_Address__c_to_BBF_Location__c_mapping.xlsx`
- [ ] Review `ES_Contact_to_BBF_Contact_mapping.xlsx`
- [ ] Review `ES_Billing_Invoice__c_to_BBF_BAN__c_mapping.xlsx`
- [ ] Review `ES_Order_to_BBF_Service__c_mapping.xlsx`
- [ ] Review `ES_OrderItem_to_BBF_Service_Charge__c_mapping.xlsx`
- [ ] Review `ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx`

### Phase 4: Day Two Enrichment
- [ ] D2-E1: Update transformer picklist maps with business decisions
- [ ] D2-E2: Test transformers
- [ ] D2-E3: Create enrichment notebooks (7 notebooks)
- [ ] D2-E4: Run enrichment notebooks (in order 01-07)
- [ ] D2-E5: Verify enrichment

---

## Support Resources

| Resource | Location |
|----------|----------|
| Migration Progress | `MIGRATION_PROGRESS.md` |
| Filtering Rules | `MIGRATION_FILTERING_GUARDRAILS.md` |
| Day Two Details | `day-two/README.md` |
| Project Config | `CLAUDE.md` |

---

**Document Version:** 4.0
**Last Updated:** 2026-01-17

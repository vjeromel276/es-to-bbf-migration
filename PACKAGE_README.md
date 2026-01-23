# Migration Package - Setup & Usage Guide

## Prerequisites

- Python 3.8+
- Access to both ES and BBF Salesforce orgs
- Required packages: `simple_salesforce`, `pandas`, `openpyxl`

```bash
pip install simple-salesforce pandas openpyxl
```

---

## Step 1: Add Your Credentials

### Initial Day Notebooks (initial-day/)

Open each `.ipynb` file and replace the credential placeholders:

```python
# ES Org
ES_USERNAME = "your_es_username"
ES_PASSWORD = "your_es_password"
ES_TOKEN = "your_es_security_token"

# BBF Org
BBF_USERNAME = "your_bbf_username"
BBF_PASSWORD = "your_bbf_password"
BBF_TOKEN = "your_bbf_security_token"
```

### Day Two Scripts (day-two/tools/)

Update credentials in these 6 files:

| File | Org | Variables |
|------|-----|-----------|
| `es_export_sf_fields.py` | ES | `sf_username`, `sf_password`, `sf_token` |
| `es_export_sf_fields_with_picklists.py` | ES | `sf_username`, `sf_password`, `sf_token` |
| `es_export_sf_picklist_values.py` | ES | `sf_username`, `sf_password`, `sf_token` |
| `bbf_export_sf_fields.py` | BBF | `sf_username`, `sf_password`, `sf_token` |
| `bbf_export_sf_fields_with_picklists.py` | BBF | `sf_username`, `sf_password`, `sf_token` |
| `bbf_export_sf_picklist_values.py` | BBF | `sf_username`, `sf_password`, `sf_token` |

---

## Step 2: Export Salesforce Metadata (Day Two)

Before creating field mappings, export metadata from both orgs:

```bash
# Export ES fields with picklist values
python day-two/tools/es_export_sf_fields_with_picklists.py

# Export BBF fields with picklist values
python day-two/tools/bbf_export_sf_fields_with_picklists.py
```

This creates CSV files in `day-two/exports/` with field metadata for each object.

---

## Step 3: Create Field Mappings (Day Two)

Run the mapping scripts to generate Excel files with AI-powered semantic matching:

```bash
# Create mapping for each object pair
python day-two/tools/create_account_mapping.py
python day-two/tools/create_address_location_mapping.py
python day-two/tools/create_contact_mapping.py
python day-two/tools/create_ban_mapping.py
# ... etc.
```

Output: Excel files in `day-two/mappings/` with two sheets:
- **Field_Mapping** - ES to BBF field matches with confidence scores
- **Picklist_Mapping** - Value translations for picklist fields

---

## Step 4: Review Mappings & Make Business Decisions

Open each mapping Excel file and review:

1. **Field_Mapping sheet**: Verify AI matches are correct (color-coded by confidence)
2. **Picklist_Mapping sheet**: For rows with "No Match - Select from list", choose the appropriate BBF value

---

## Step 5: Generate Transformer Functions (Day Two)

After reviewing mappings, generate Python transformer functions:

```bash
python day-two/tools/generate_transformers.py --all
```

This creates/updates files in `day-two/transformers/` with functions to convert ES values to BBF format.

---

## Step 6: Run Initial Day Migration

Execute notebooks in order (dependencies matter):

1. `01_location_migration.ipynb`
2. `02_account_migration.ipynb`
3. `03_contact_migration.ipynb`
4. `04_ban_migration.ipynb`
5. `05_service_migration.ipynb`
6. `06_service_charge_migration.ipynb`
7. `07_offnet_migration.ipynb`

Each notebook has a **dry run** mode (default) - set `DRY_RUN = False` to execute actual inserts.

---

## Directory Structure

```
migration-package/
├── initial-day/                    # Day 1 migration notebooks
│   ├── 01_location_migration.ipynb
│   ├── 02_account_migration.ipynb
│   ├── 03_contact_migration.ipynb
│   ├── 04_ban_migration.ipynb
│   ├── 05_service_migration.ipynb
│   ├── 06_service_charge_migration.ipynb
│   └── 07_offnet_migration.ipynb
│
└── day-two/                        # Day 2 enrichment tools
    ├── README.md                   # Detailed documentation
    ├── tools/                      # Automation scripts
    │   ├── es_export_sf_*.py       # ES metadata exporters
    │   ├── bbf_export_sf_*.py      # BBF metadata exporters
    │   ├── create_*_mapping.py     # Mapping generators
    │   ├── generate_transformers.py
    │   └── recommend_picklist_values.py
    └── transformers/               # Field transformation functions
        ├── account_transformers.py
        ├── location_transformers.py
        ├── contact_transformers.py
        ├── ban_transformers.py
        ├── service_transformers.py
        ├── service_charge_transformers.py
        └── off_net_transformers.py
```

---

## Notes

- **exports/** and **mappings/** folders are not included - they will be regenerated when you run the scripts
- All credentials have been removed - you must add your own
- The transformers are pre-generated but will be regenerated if you run `generate_transformers.py`

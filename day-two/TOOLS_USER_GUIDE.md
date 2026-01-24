# Day Two Tools User Guide

**Last Updated**: 2026-01-24

This guide documents all tools and workflows for Day Two field enrichment.

---

## Quick Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `sync_picklist_mappings.py` | Sync picklist values with ES_Final_Field | After business changes ES_Final_Field |
| `recommend_picklist_values.py` | AI recommendations for picklist translations | After sync, to auto-fill matches |
| `generate_transformers.py` | Generate Python transformer functions | After mapping finalized |
| `mapping_reader.py` | Read mappings in notebooks | In enrichment notebooks |

---

## Workflow: After Business Updates ES_Final_Field

When a business owner changes `ES_Final_Field` in a mapping Excel file (e.g., changing the source field for a BBF field), run these steps:

### Step 1: Sync Picklist Mappings

```bash
python day-two/tools/sync_picklist_mappings.py --mapping ES_Account_to_BBF_Account_mapping.xlsx
```

**What it does:**
- Reads `ES_Final_Field` from Field_Mapping sheet
- Queries ES Salesforce for actual picklist values of that field
- Updates Picklist_Mapping sheet with correct ES field and values
- Populates `Suggested_Mapping` with available BBF picklist values
- Preserves existing `BBF_Final_Value` translations

**Options:**
- `--dry-run` - Preview changes without modifying Excel
- `--all` - Process all mapping files

### Step 2: Run AI Recommendations

```bash
python day-two/tools/recommend_picklist_values.py --input day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx
```

**What it does:**
- Finds rows with `Notes = "No Match"`
- Uses semantic matching to recommend BBF values
- Fills in `BBF_Final_Value` for exact and close matches
- Adds `AI_Confidence` and `AI_Reasoning` columns

**Options:**
- `--dry-run` - Preview recommendations without updating
- `--all` - Process all mapping files

### Step 3: Business Review

Open the Excel file and review:
1. AI recommendations (check `AI_Confidence` and `AI_Reasoning`)
2. Rows still needing `BBF_Final_Value` (manual decision required)

---

## Workflow: Generate Transformer Functions

After mapping is finalized and picklist translations are complete:

```bash
# Single file
python day-two/tools/generate_transformers.py --mapping day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx

# All files
python day-two/tools/generate_transformers.py --all
```

**What it does:**
- Reads Field_Mapping sheet for `Transformer_Needed = Y` rows
- Generates Python functions in `day-two/transformers/`
- Creates picklist translation dictionaries from Picklist_Mapping sheet

**Output:** `day-two/transformers/{object}_transformers.py`

---

## Workflow: Run Enrichment

### Using mapping_reader.py in Notebooks

```python
import sys
sys.path.insert(0, 'day-two')
from mapping_reader import load_mapping, get_enrichment_fields, translate_picklist

# Load mapping
mapping = load_mapping('ES_Account_to_BBF_Account_mapping.xlsx')

# Get fields to enrich (respects Include_in_Migration and ES_Final_Field)
DAY1_FIELDS = ['Name', 'BillingStreet', ...]  # Fields already migrated
enrichment_fields = get_enrichment_fields(mapping, exclude_day1_fields=DAY1_FIELDS)

# Translate a picklist value
bbf_value = translate_picklist(mapping, 'Type', es_record['Business_Sector__c'])
```

**Key behaviors:**
- Uses `ES_Final_Field` when valid, falls back to `ES_Field_API_Name`
- Excludes fields where `Include_in_Migration = No`
- Excludes deprecated fields (label contains "(dep)")

---

## Tool Reference

### sync_picklist_mappings.py

**Location:** `day-two/tools/sync_picklist_mappings.py`

**Purpose:** Synchronize Picklist_Mapping sheet with actual ES field values when ES_Final_Field changes.

**Usage:**
```bash
# Sync single file
python day-two/tools/sync_picklist_mappings.py --mapping ES_Account_to_BBF_Account_mapping.xlsx

# Sync all files
python day-two/tools/sync_picklist_mappings.py --all

# Preview only
python day-two/tools/sync_picklist_mappings.py --mapping ES_Account_to_BBF_Account_mapping.xlsx --dry-run
```

**Input:** Mapping Excel file with Field_Mapping and Picklist_Mapping sheets

**Output:** Updated Picklist_Mapping sheet with:
- Correct `ES_Field` values
- `ES_Picklist_Value` from ES Salesforce
- `Suggested_Mapping` with BBF options (pipe-separated)
- Preserved `BBF_Final_Value` where applicable

---

### recommend_picklist_values.py

**Location:** `day-two/tools/recommend_picklist_values.py`

**Purpose:** AI-powered semantic matching for picklist value translations.

**Usage:**
```bash
# Process single file
python day-two/tools/recommend_picklist_values.py --input day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx

# Process all files
python day-two/tools/recommend_picklist_values.py --all

# Preview only
python day-two/tools/recommend_picklist_values.py --input day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx --dry-run
```

**Matching Logic:**
1. Exact match (case-insensitive) → 100%
2. Semantic equivalence (e.g., "Paper" → "Print") → 95%
3. Spacing differences (e.g., "NET30" → "NET 30") → 90%
4. Word similarity → varies
5. Substring match → 60%

**Output:** Updated `BBF_Final_Value`, `AI_Confidence`, `AI_Reasoning` columns

---

### generate_transformers.py

**Location:** `day-two/tools/generate_transformers.py`

**Purpose:** Auto-generate Python transformer functions from mapping Excel files.

**Usage:**
```bash
# Generate for single mapping
python day-two/tools/generate_transformers.py --mapping day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx

# Generate for all mappings
python day-two/tools/generate_transformers.py --all

# Preview only
python day-two/tools/generate_transformers.py --mapping day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx --dry-run
```

**Output:** Python modules in `day-two/transformers/` with:
- Picklist mapping dictionaries
- Transform functions for each field
- `TRANSFORMERS` registry dict
- `apply_transformers(es_record)` batch function

---

### mapping_reader.py

**Location:** `day-two/mapping_reader.py`

**Purpose:** Utility module for reading mapping Excel files in enrichment notebooks.

**Key Functions:**

```python
# Load a mapping file
mapping = load_mapping('ES_Account_to_BBF_Account_mapping.xlsx')

# Get enrichable fields (dict of BBF_field -> ES_field)
fields = get_enrichment_fields(mapping, exclude_day1_fields=['Name', 'Id'])

# Translate a picklist value
bbf_value = translate_picklist(mapping, 'Type', 'Enterprise')

# Check if field is deprecated
is_dep = is_deprecated_field('(dep) Old Field')

# Print summary
print_mapping_summary(mapping)
```

**Field Selection Logic:**
1. Uses `ES_Final_Field` if valid API name, else `ES_Field_API_Name`
2. Excludes `Include_in_Migration = No`
3. Excludes deprecated fields (label contains "(dep)")
4. Only includes High/Medium confidence matches

---

## Excel Mapping File Structure

### Field_Mapping Sheet

| Column | Description |
|--------|-------------|
| BBF_Field_API_Name | Target BBF field |
| BBF_Field_Label | BBF field label |
| BBF_Data_Type | BBF field type |
| ES_Field_API_Name | Original AI-matched ES field |
| **ES_Final_Field** | Business-approved ES source field (overrides ES_Field_API_Name) |
| **Include_in_Migration** | Yes/No - whether to include in enrichment |
| Match_Confidence | High/Medium/Low/None |
| Transformer_Needed | Y/N |

### Picklist_Mapping Sheet

| Column | Description |
|--------|-------------|
| BBF_Field | Target BBF field |
| ES_Field | Source ES field |
| ES_Picklist_Value | Value from ES |
| Suggested_Mapping | Available BBF values (pipe-separated) |
| BBF_Final_Value | Translated BBF value |
| AI_Confidence | Confidence % (if AI-recommended) |
| AI_Reasoning | Explanation (if AI-recommended) |
| Notes | Status (Preserved, No Match, etc.) |

---

## Troubleshooting

### Sync tool says "No BBF picklist export found"

Run the BBF export tool first:
```bash
python day-two/tools/bbf_export_sf_picklist_values.py --object Account --output-dir day-two/exports
```

### Recommendation tool makes 0 recommendations

Check that `Suggested_Mapping` column has BBF values. Run sync first:
```bash
python day-two/tools/sync_picklist_mappings.py --mapping <file>.xlsx
```

### mapping_reader uses wrong ES field

Ensure `ES_Final_Field` contains a valid API name (no spaces). The tool validates:
- No spaces in name
- Ends with `__c` OR matches standard field pattern

---

## Version History

| Date | Changes |
|------|---------|
| 2026-01-24 | Added sync_picklist_mappings.py tool |
| 2026-01-24 | mapping_reader.py now uses ES_Final_Field |
| 2026-01-24 | mapping_reader.py respects Include_in_Migration |
| 2026-01-24 | Initial user guide created |

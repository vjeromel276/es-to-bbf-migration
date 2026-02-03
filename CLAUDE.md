# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

ES-to-BBF Salesforce data migration: migrating data from the EverStream (ES) Salesforce org into the BlueBird Fiber (BBF) Salesforce org. ES was acquired by BBF; this consolidates CRM data.

**AT THE START OF EVERY NEW CHAT**: Read recent git commits (`git log --oneline -20`) to understand what changed recently. Verify field names and metadata against actual Salesforce before writing migration code.

## Architecture

### Two-Phase Migration

- **Day 1 (`initial-day/`)**: Created records with required fields only. 8 numbered notebooks (00-08) executed in dependency order. **Complete.**
- **Day 2 (`day-two/`)**: Enriches those records with optional fields using field mappings, transformer functions, and picklist translations. 7 enrichment notebooks (01-07). **In progress** -- pending business review of picklist values.

### Migration Order (Dependency Chain)

```
Wave 0: BAN Prep (mark BANs with BBF_Ban__c = true)
Wave 1: Location__c (from Address__c), Account -- no dependencies
Wave 2: Contact (needs Account), BAN__c (needs Account)
Wave 3: Service__c (needs BAN master-detail), Service_Charge__c (needs Service), Off_Net__c (needs Service + Location)
```

### Core Filtering Rules

Every migration query MUST enforce:
- `Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')`
- `Project_Group__c NOT LIKE '%PA MARKET DECOM%'`
- `Billing_Invoice__r.BBF_Ban__c = true`

### Bidirectional ID Tracking

- BBF records store `ES_Legacy_ID__c` = original ES record Id
- ES records store `BBF_New_Id__c` = new BBF record Id
- All notebooks check for existing `ES_Legacy_ID__c` before inserting to prevent duplicates

## Key Files

| Path | Purpose |
|------|---------|
| `NOTEBOOK_CHANGELOG.md` | Change log for migration notebook updates (track field additions, query changes) |
| `day-two/mapping_reader.py` | Utility for loading mapping Excel files, extracting enrichment fields, translating picklist values, filtering deprecated fields |
| `day-two/transformers/*.py` | 81 auto-generated transformer functions (picklist maps, type conversions). Each module has `TRANSFORMERS` dict and `apply_transformers()` |
| `day-two/mappings/*.xlsx` | Field mapping Excel files (gitignored). Two sheets: `Field_Mapping` and `Picklist_Mapping` |
| `day-two/tools/generate_transformers.py` | Reads mapping Excel, generates transformer Python modules. Use `--all` or `--mapping <file>` |
| `day-two/tools/sync_picklist_mappings.py` | Re-queries ES for picklist values when `ES_Final_Field` changes in mapping Excel |
| `day-two/tools/create_mapping_excel.py` | Generates formatted two-sheet Excel mapping files with color coding |
| `initial-day/08_es_product_mapping_export.ipynb` | Exports ES Product/OrderItem data with bandwidth for Service_Charge mapping (14 CSV columns) |

## Salesforce Connection Pattern

All scripts use `simple_salesforce.Salesforce` with username/password/security_token auth. Credentials are hardcoded in notebooks (not in env vars). Two orgs:
- **ES org**: source data (`es_sf` variable convention)
- **BBF org**: target data (`bbf_sf` variable convention)
- Domain is `"test"` for sandbox, `"login"` for production

## Day 2 Enrichment Pattern

Each enrichment notebook follows this flow:
1. Load field mapping from Excel via `mapping_reader.load_mapping()`
2. Get enrichment fields via `get_enrichment_fields()` (auto-excludes deprecated fields)
3. Query BBF records that have `ES_Legacy_ID__c` set
4. Query matching ES source records
5. For each field pair, apply transformer or picklist translation if needed
6. Bulk update BBF records with enriched values
7. Export results to Excel

## Day 1 Notebook Structure (10 cells)

1. Overview markdown (prerequisites, field mapping table)
2. Setup & imports
3. Configuration (TEST_MODE, credentials, filters, OWNER_ID)
4. Connect to both SF orgs
5. Query source + duplicate prevention check
6. Transform data (field mapping, lookups)
7. Insert to BBF (bulk API)
8. Update ES with BBF_New_Id__c
9. Excel output (4 sheets: Results, Summary, ID Mapping, Failed Inserts)
10. Summary + next steps

## Transformer Module Structure

Each `day-two/transformers/*_transformers.py` contains:
- Picklist value maps as module-level dicts (e.g., `INDUSTRY_MAP = {...}`)
- Individual `transform_FieldName(es_value, context=None)` functions
- `TRANSFORMERS` dict mapping BBF field names to transform functions
- `FIELD_MAPPING` dict mapping BBF field names to ES field names
- `apply_transformers(es_record)` function that applies all transforms

## Conventions

- **Notebook naming**: `NN_objectname_migration.ipynb` (Day 1), `NN_objectname_enrichment.ipynb` (Day 2)
- **Mapping files**: `ES_{ESObject}_to_BBF_{BBFObject}_mapping.xlsx`
- **Output files**: `es_bbf_{object}_migration_{timestamp}.xlsx`
- **Config constants**: UPPER_SNAKE_CASE (`TEST_MODE`, `FILTER_BY_BBF_BAN`)
- **SF field names**: Must be exact -- case-sensitive. Always verify against metadata before using.

## Dependencies

`simple_salesforce`, `pandas`, `openpyxl` -- no requirements.txt exists.

## What's Gitignored

`*.xlsx`, `*.csv`, `*.log`, `*.docx`, `*.zip`, `__pycache__/` -- all Excel mappings, exports, and migration outputs are local only.

## Claude Agents

Six agents in `.claude/agents/` handle specialized workflows:
- `day-two-field-mapping` -- AI semantic field matching, generates mapping Excel files
- `transformation-generator` -- reads mapping Excel, generates transformer Python modules
- `es-bbf-migration-pm` -- project manager, knows migration order and required fields
- `migration-docs-sync` -- keeps docs in sync with notebook code
- `migration-progress-tracker` -- maintains progress log
- `tools-guide-updater` -- keeps TOOLS_USER_GUIDE.md current

## Critical Rules

- Verify BBF field names are EXACT (case-sensitive) before writing any migration code
- Check if fields exist, check nillability, check if Name is autonumber, check if OwnerId exists on the object
- Boolean fields default to False in Salesforce -- don't explicitly set them unless True
- Always use `ES_Legacy_ID__c` for duplicate prevention before inserting
- Deprecated fields (label contains "(dep)" or `Deprecated=Y` in mapping) must be excluded from enrichment

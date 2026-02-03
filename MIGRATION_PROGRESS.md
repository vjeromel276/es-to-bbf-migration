# Migration Progress Log

## Project Overview
- **Migration Name**: ES-to-BBF Salesforce Data Migration
- **Start Date**: 2024 (based on git history)
- **Target Completion**: TBD (pending business review of picklist values)
- **Current Phase**: Day 2 Enrichment (in progress)

## Quick Status Summary
- **Overall Progress**: 60% complete
- **Last Session**: 2026-02-02 - Enhanced product mapping export with bandwidth data
- **Next Priority**: Complete Day 2 enrichment notebooks pending business picklist review

## Completed Work

### Phase: Day 1 Initial Migration (Complete)
All Day 1 migration notebooks (00-08) have been executed successfully:
- Wave 0: BAN Prep (UAT sandbox)
- Wave 1: Location (from Address), Account
- Wave 2: Contact, BAN
- Wave 3: Service, Service_Charge, Off_Net
- Wave 4: Product mapping export

**Key accomplishments:**
- Established bidirectional ID tracking (ES_Legacy_ID__c, BBF_New_Id__c)
- Implemented core filtering rules for all migrations
- Created required field migrations with duplicate prevention
- Successfully migrated 7 core objects in dependency order

### 2026-02-02 - Product Mapping Export Enhancement
**File Modified**: `initial-day/08_es_product_mapping_export.ipynb`

**Changes:**
- Added `Bandwidth_NEW__c` field from OrderItem to the export query
- CSV export now includes a "Bandwidth" column for product mapping analysis
- Documented alternative bandwidth field: `Service_Provided__c` on Order (not used in this implementation)

**Rationale**: Support enhanced product mapping analysis by including bandwidth information in the export data.

### Recent Tooling & Infrastructure Updates (January 2026)
- Created `day-two/tools/sync_picklist_mappings.py` - Re-queries ES for picklist values when ES_Final_Field changes in mapping Excel
- Created `TOOLS_USER_GUIDE.md` and `tools-guide-updater` agent for documentation maintenance
- Fixed `mapping_reader.py` to properly respect Include_in_Migration column
- Updated all Day 2 enrichment notebooks to use Excel mapping files and exclude deprecated fields
- Generated 81 transformer modules for picklist mapping and type conversions
- Created 7 enrichment notebooks for all migrated objects

### Mapping & Transformation Infrastructure
- Established two-sheet Excel mapping pattern (Field_Mapping, Picklist_Mapping)
- Built `day-two/mapping_reader.py` utility for loading mappings and translating picklist values
- Created `day-two/tools/generate_transformers.py` for auto-generating transformer Python modules
- Created `day-two/tools/create_mapping_excel.py` for generating formatted mapping files

## In Progress

### Day 2 Enrichment Phase
**Status**: Infrastructure complete, waiting on business review

**Created but pending execution:**
- 01_location_enrichment.ipynb
- 02_account_enrichment.ipynb
- 03_contact_enrichment.ipynb
- 04_ban_enrichment.ipynb
- 05_service_enrichment.ipynb
- 06_service_charge_enrichment.ipynb
- 07_offnet_enrichment.ipynb

**Blocker**: Pending business stakeholder review of picklist value mappings before executing enrichment migrations.

## Pending/Blocked

### Blocked Items
- **All Day 2 enrichment execution** - Blocked by: Business review of picklist mappings required
- **Production migration** - Blocked by: Day 2 enrichment completion

### To Be Started
- Data validation and reconciliation after Day 2 enrichment
- Production migration planning and execution
- Post-migration cleanup and ES org decommissioning planning

## Issues & Decisions Log

### Decision: Use Bandwidth_NEW__c over Service_Provided__c
**Date**: 2026-02-02  
**Context**: Product mapping export needed bandwidth information  
**Decision**: Use `Bandwidth_NEW__c` from OrderItem instead of `Service_Provided__c` from Order  
**Rationale**: More granular data at the OrderItem level; Service_Provided__c documented as alternative but not selected for this use case

### Decision: Two-Phase Migration Approach
**Date**: Early project phase  
**Context**: Managing complexity and risk  
**Decision**: Split migration into Day 1 (required fields) and Day 2 (enrichment)  
**Rationale**: Reduces initial migration risk, allows for business validation of picklist mappings, enables rollback if needed

### Decision: Bidirectional ID Tracking
**Date**: Early project phase  
**Context**: Need to prevent duplicates and enable updates  
**Decision**: ES records get BBF_New_Id__c, BBF records get ES_Legacy_ID__c  
**Rationale**: Enables duplicate prevention, supports enrichment lookups, provides audit trail

### Technical Note: Deprecated Field Handling
**Date**: January 2026  
**Issue**: Some mapping files included deprecated fields causing migration errors  
**Solution**: Enhanced mapping_reader.py to auto-exclude fields with "(dep)" in label or Deprecated=Y  
**Impact**: Prevents migration failures from attempting to update read-only or non-existent fields

## Session History

| Date | Duration | Focus Area | Key Accomplishments |
|------|----------|------------|--------------------|
| 2026-02-02 | Short | Product Mapping Export | Added Bandwidth_NEW__c field to 08_es_product_mapping_export.ipynb CSV export |
| Jan 2026 | Multiple sessions | Day 2 Infrastructure | Created all enrichment notebooks, transformer generation tools, picklist sync tools, documentation |
| Dec 2025 - Jan 2026 | Multiple sessions | Day 1 Migration | Executed all initial migration notebooks (00-08) successfully in sandbox |
| 2024-2025 | Multiple sessions | Project Setup | Established architecture, migration patterns, connection patterns, filtering rules |

## Notes & Open Questions

### Open Questions
- When will business stakeholders complete picklist mapping review?
- What is the target date for production migration?
- Are there any additional fields that need to be added to product mapping export?

### Technical Debt
- No requirements.txt file exists (dependencies: simple_salesforce, pandas, openpyxl)
- Credentials are hardcoded in notebooks (not environment variables)
- All mapping files and exports are gitignored (local only)

### Success Metrics to Track
- Record counts by object (ES source vs BBF target)
- Field population rates after enrichment
- Picklist value translation coverage
- Failed record counts and reasons

---
*Last updated: 2026-02-02*

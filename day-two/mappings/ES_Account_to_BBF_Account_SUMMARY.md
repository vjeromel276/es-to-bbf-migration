# Account → Account Field Mapping Summary

**Date**: 2026-01-15
**Source Org**: EverStream (ES)
**Target Org**: Bluebird Fiber (BBF)
**Output File**: `ES_Account_to_BBF_Account_mapping.xlsx`

---

## Overview

This mapping document maps **150 BBF Account fields** to their corresponding ES Account source fields for the Day Two enrichment phase of the data migration.

### Fields Excluded from Mapping

**System Fields** (auto-managed by Salesforce):
- Id, IsDeleted, MasterRecordId
- CreatedDate, CreatedById, LastModifiedDate, LastModifiedById, SystemModstamp
- LastActivityDate, LastViewedDate, LastReferencedDate
- JigsawContactId, Jigsaw, PhotoUrl, CleanStatus

**Day 1 Fields** (already handled in initial migration):
- Name
- OwnerId
- ES_Legacy_ID__c
- BBF_New_Id__c

---

## Field Mapping Statistics

### Overall Confidence Distribution

| Confidence Level | Count | Percentage | Description |
|-----------------|-------|------------|-------------|
| **High** | 40 | 26.7% | Strong match - API name/label similar with compatible types |
| **Medium** | 47 | 31.3% | Moderate match - Similar API name or label |
| **Low** | 2 | 1.3% | Weak match - Semantic similarity only |
| **None** | 61 | 40.7% | No obvious ES field found - needs business rule or default |
| **TOTAL** | 150 | 100% | |

### Transformation Requirements

- **Transformers Needed**: 42 fields (28%)
- **Direct Mapping**: 108 fields (72%)

**Transformers are needed when:**
- Data types differ (e.g., ES text → BBF picklist)
- Field lengths differ (ES field longer than BBF)
- Picklist values don't have exact matches
- Low/No confidence match requires custom logic

---

## Picklist Value Mapping Statistics

### Overall Picklist Value Distribution

| Match Type | Count | Percentage | Description |
|-----------|-------|------------|-------------|
| **Exact Match** | 38 | 55.1% | ES value exists in BBF picklist (no transformation needed) |
| **Suggested Match** | 1 | 1.4% | Close match found (case-insensitive or similar) |
| **No Match** | 30 | 43.5% | No match - requires business decision |
| **TOTAL** | 69 | 100% | |

### Picklist Fields Requiring Business Review

**30 picklist values** require business stakeholder decisions because:
- ES value does not exist in BBF picklist
- Multiple ES values may map to single BBF value
- Business rules needed to determine correct BBF value

---

## Excel Workbook Structure

### Sheet 1: Field_Mapping

**Columns:**
1. **BBF_Field_API_Name** - Target field API name in BBF
2. **BBF_Field_Label** - Target field label in BBF
3. **BBF_Data_Type** - BBF field data type
4. **BBF_Is_Required** - Is the field required? (Yes/No)
5. **ES_Field_API_Name** - Source field API name in ES
6. **ES_Field_Label** - Source field label in ES
7. **ES_Data_Type** - ES field data type
8. **Match_Confidence** - High / Medium / Low / None
9. **Transformer_Needed** - Y / N
10. **Notes** - Detailed explanation of mapping logic

**Color Coding:**
- 🟢 Green = High Confidence Match
- 🟡 Yellow = Medium Confidence Match
- 🔴 Red = Low Confidence Match
- ⚫ Gray = No Match Found

### Sheet 2: Picklist_Mapping

**NEW FORMAT - Left-to-Right Workflow:**

**Columns:**
1. **ES_Field** - ES source picklist field API name
2. **ES_Picklist_Value** - ES source value to map
3. **BBF_Field** - BBF target picklist field API name
4. **Suggested_Mapping** - Either:
   - The exact BBF value match, OR
   - Complete list of all valid BBF values separated by " | " (no truncation)
5. **Notes** - Match type indicator:
   - "Exact Match" - ES value exists in BBF
   - "Close Match" - Similar value found
   - "No Match - Select from list" - User must choose from provided list
6. **BBF_Final_Value** - EMPTY - User decision column for final mapping

**Color Coding:**
- 🟢 Green = Exact Match
- 🟡 Yellow = Close Match
- 🔴 Red = No Match (Review Required)

**Important**: When "No Match" occurs, the Suggested_Mapping column shows the COMPLETE list of valid BBF values (never uses "..."). Users can copy/paste the desired value into the BBF_Final_Value column.

---

## Key Findings

### High-Confidence Matches (40 fields)

These fields can be migrated with minimal risk:
- Standard Salesforce fields (Phone, Fax, Website, etc.)
- Common business fields (AnnualRevenue, NumberOfEmployees, etc.)
- Fields with exact API name matches across orgs

### Fields Requiring Business Rules (61 fields)

These BBF fields have no obvious ES source:
- BBF-specific custom fields
- Fields that may need calculated values
- Fields that may need default values
- Fields that may need manual data entry post-migration

### Critical Picklist Mappings Requiring Review (30 values)

**Examples of picklist mapping challenges:**

1. **Type Field**:
   - ES: "Enterprise", "Wholesale", "Wholesale Wireless"
   - BBF: "Customer", "Sales Prospect", "Vendor", "Customer (MDU Residential)", "Other", "Customer (Wholesaler Carrier)"
   - Action needed: Map ES wholesale types to appropriate BBF customer types

2. **Industry Field**:
   - ES has 27 industry vertical values
   - BBF has 21 industry values
   - Some ES values (e.g., "Carrier", "CLEC/ILEC", "Internet Provider") may need mapping to BBF equivalents

3. **AccountSource Field**:
   - ES has 21 source values
   - BBF has 11 source values
   - Significant overlap but many ES-specific sources need mapping decisions

---

## Recommended Next Steps

### 1. Field Mapping Review (Priority: HIGH)

**Action**: Review all fields marked "None" or "Low" confidence
**Assignee**: Data migration team + Business stakeholders
**Output**: Document which BBF fields should receive:
- Mapped values from ES
- Calculated/derived values
- Default values
- Manual entry post-migration
- Null values (acceptable)

### 2. Picklist Value Mapping (Priority: CRITICAL)

**Action**: For all 30 "No Match" picklist values in Sheet 2:
1. Open the Excel file
2. Review each red-highlighted row
3. Select the appropriate BBF value from the Suggested_Mapping list
4. Copy/paste into BBF_Final_Value column
5. Document any business logic in Notes if needed

**Assignee**: Business stakeholders + Data migration team
**Timeline**: Before Day Two enrichment scripts are built

### 3. Transformer Development (Priority: MEDIUM)

**Action**: Build 42 data transformers for fields marked "Y" in Transformer_Needed column
**Assignee**: Data migration development team
**Dependencies**: Steps 1 & 2 must be completed first

---

## Usage Instructions

### For Business Stakeholders

1. **Open Excel file**: `ES_Account_to_BBF_Account_mapping.xlsx`
2. **Review Sheet 1 (Field_Mapping)**:
   - Focus on Yellow, Red, and Gray rows
   - Validate that suggested ES → BBF mappings make business sense
   - Add comments/notes for any concerns
3. **Review Sheet 2 (Picklist_Mapping)**:
   - Focus on Red rows (No Match)
   - For each row, copy the correct BBF value from column D (Suggested_Mapping) into column F (BBF_Final_Value)
   - If none are appropriate, add a note explaining what value should be used

### For Data Migration Team

1. Use Sheet 1 to understand field relationships
2. Use Sheet 2 (after stakeholder review) to build picklist value translation maps
3. Build transformers for fields marked "Y" in Transformer_Needed
4. Validate mapping logic with business stakeholders
5. Test enrichment scripts with sample data before full migration

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-15 | v2 | Updated picklist format with new column order, complete value lists, left-to-right workflow |
| 2026-01-15 | v1 | Initial mapping with system/Day 1 field exclusions |

---

## Contact

For questions about this mapping document:
- **Data Migration Team**: Review field mapping logic and transformer requirements
- **Business Stakeholders**: Review picklist value mappings and business rule requirements
- **Salesforce Admins**: Validate field metadata and data type compatibility

---

*Document generated by Day Two Field Mapping Agent*
*EverStream → Bluebird Fiber Data Migration Project*

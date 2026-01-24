# Off_Net__c to Off_Net__c Field Mapping Summary

**Date**: 2026-01-15
**Source Object**: ES Off_Net__c (EverStream)
**Target Object**: BBF Off_Net__c (Bluebird Fiber)
**Mapping Type**: AI-Powered Semantic Matching with Telecom Off-Net Domain Knowledge

## Executive Summary

This mapping document covers the Day 2 field enrichment for Off_Net__c records, which track third-party carrier circuits and vendor-provided services. The ES Off_Net__c object is significantly more comprehensive (94 fields) than BBF Off_Net__c (49 fields), reflecting ES's more extensive vendor order and project management tracking.

**Key Statistics:**
- **BBF Fields**: 33 (after excluding 16 system/Day 1 fields)
- **High Confidence Matches**: 15 (45%)
- **Medium Confidence Matches**: 4 (12%)
- **Low Confidence Matches**: 11 (33%)
- **No Match (BBF-only)**: 3 (9%)
- **Transformers Needed**: 12 (36%)

## AI Semantic Matching Approach

This mapping was generated using AI-powered semantic analysis with deep understanding of:
- Telecom off-net and vendor circuit management concepts
- Cost of Goods Sold (COGS) tracking for third-party services
- Vendor order lifecycle (PON, FOC, disconnect, ETL)
- Service disconnect and early termination liability (ETL) management
- Vendor relationship and billing account management

The AI matching identified field purposes based on meaning and telecom domain knowledge, not just string similarity.

## Migration Strategy

### Day 1 (Already Completed)
- Migrated required fields only: `Name` (autonumber), `OwnerId`, `Service__c` (lookup), location lookups
- Created shell Off_Net__c records with relationships established
- **Result**: 6 Off_Net records migrated successfully in POC

### Day 2 (This Mapping - Enrichment)
- Populate all matched fields from ES to BBF
- Apply transformers for data type conversions
- Map picklist values between orgs
- Leave BBF-specific fields for manual population

## Field Categories

### High Confidence - Core COGS and Vendor Tracking (15 fields)

These fields have exact or near-exact semantic matches and represent the core purpose of off-net tracking:

#### COGS (Cost of Goods Sold)
- `COGS_MRC__c` ← `Cost_MRC__c` (Monthly recurring vendor costs)
- `COGS_NRC__c` ← `Cost_NRC__c` (Non-recurring vendor costs)

#### Circuit Identification
- `Off_Net_Circuit_ID__c` ← `Vendor_circuit_Id__c` (Primary vendor circuit identifier)

#### Disconnect Management
- `Disconnect_Date__c` ← `Disconnect_Date__c` (Service termination date)
- `Disconnect_Submitted_Date__c` ← `PM_Order_Completed__c` (Disconnect request submitted)
- `Disconnect_PON__c` ← `Disconnect_PON__c` (Disconnect purchase order)
- `Future_Disconnect_Date__c` ← `Future_Disconnect_Date__c` (Scheduled future disconnect)

#### Vendor Dates and Order Tracking
- `Off_Net_Service_Due_Date__c` ← `Vendor_Due_date__c` (Vendor-committed due date)
- `Off_Net_Start_Date__c` ← `Vendor_Bill_Start_Date__c` (Vendor billing start)
- `Vendor_Order_Issued__c` ← `Vendor_Order_Issued__c` (Vendor order issued date)

#### Vendor References
- `Vendor_BAN__c` ← `Vendor_Ban__c` (Vendor billing account - requires lookup)
- `Vendor_PON__c` ← `VendorPON__c` (Vendor purchase order number)

#### Early Termination Liability (ETL) Tracking
- `Approved_ETL_Disconnect_Date__c` ← `Approved_ETL_Disconnect_Date__c`
- `ETL_Amount_Approved__c` ← `ETL_Amount_Approved__c`

#### Contract Term
- `Term__c` ← `Term__c` (Contract term in months - **requires picklist mapping**)

### Medium Confidence - Status and Problem Tracking (4 fields)

These fields have semantic alignment but require value translation or have context differences:

- `Off_Net_Service_Status__c` ← `LEC_Order_Status__c`
  - **Transformer needed**: Picklist value mapping (ES: "Pending", "Active", "NOC Review" → BBF: "Pending", "Active", "NOC Reiew" [sic])

- `Off_Net_Problem_Reason_Code__c` ← `Off_Net_Problem_Reason_Code__c`
  - **Note**: Identical picklist values (7 exact matches), but used in different contexts

- `Off_Net_Original_Due_Date__c` ← `Vendor_FOC_Received__c`
  - **Note**: Semantic match but different purposes (original due vs FOC received)

- `Stripped_Circuit_ID__c` ← `Stripped_Circuit_ID2__c`
  - **Note**: Similar purpose but different implementations

### Low Confidence - Vendor Details and Notes (11 fields)

These fields have matches but require significant transformation or have ambiguous purpose:

#### Vendor Provider Fields (Type Mismatch)
- `Aloc_COGS_Provider__c` ← `Off_Net_Vendor__c` (A-Location provider - reference to text)
- `Zloc_COGS_Provider__c` ← `Vendor_Name__c` (Z-Location provider - reference to text)
- `Vendor_NNI__c` ← `Vendor_NNI__c` (Vendor NNI - reference to text)

#### Circuit and Order Details
- `BBF_Circuit_ID__c` ← `Internal_Circuit_Id__c` (BBF circuit ID - requires truncation)
- `Demarc_Location__c` ← `Demarc_Loaction__c` (Demarc location - note ES typo)
- `Order_Number__c` ← `Vendor_Order__c` (Order number text field)

#### Notes and Problem Tracking
- `Additional_Information__c` ← `Notes__c` (Additional information text)
- `Off_Net_Problem_Reason__c` ← `Off_Net_Problem_Reason__c` (Problem reason details)
- `Review_Requested_Date__c` ← `Requested_ETL_Review_Date__c` (ETL review date)

#### Product and Service Type (Complex Picklist Mapping)
- `Product__c` ← `Bandwidth__c`
  - **Challenge**: BBF has 471 product values vs ES 43 bandwidth values
  - **Transformer needed**: Business rules for bandwidth → product mapping

- `Service_Type__c` ← `Off_Net_Type__c`
  - **Challenge**: BBF has 72 service types vs ES 3 off-net types
  - **Transformer needed**: Business rules for type expansion

### No Match - BBF-Specific Fields (3 fields)

These fields exist only in BBF and have no ES source:

- `Charge_Class__c` (RECUR/NONRECUR/TAX/ANNUALLY)
  - **Action**: Derive from service type or leave for manual entry

- `Service_Order_Line__c` (Link to service order line)
  - **Action**: Likely not needed for ES migration

- `Off_Net_Expiration_Date__c` (Calculated contract expiration)
  - **Action**: Formula field - auto-calculated by BBF

## Picklist Mappings

### Term__c (Contract Term) - Picklist to Picklist

**ES Values → BBF Values:**
- Exact matches (9 values): 12, 24, 36, 48, 60, 84, 96, 120, 240 months
- BBF additional values: 0, 1, 72, 108, 132, 144, 156, 168, 180, 192, 204, 216, 228, 516, "Not Renewing"
- ES unique values: 6, 18, 62, "NO" (no term), "MO" (month-to-month)

**Business Decision Needed:**
- ES "NO" → BBF "0" or "Not Renewing"?
- ES "MO" → BBF "1" (month-to-month) or leave blank?
- ES 6, 18, 62 → Map to nearest BBF value or add to BBF picklist?

### Off_Net_Service_Status__c (Service Status) - LEC_Order_Status__c

**ES Values → BBF Values:**
- Exact matches: "Pending", "Active", "Soft Disco", "Pending Disco", "Invoice Evaluation", "Disco"
- Close match: "NOC Review" → "NOC Reiew" (typo in BBF - suggest fixing BBF typo)

### Off_Net_Problem_Reason_Code__c (Problem Reason Code)

**All 7 values are exact matches:**
- Customer Readiness
- Pending MSA/Contract
- Related Order Dependency
- Pending ETL Approval
- Pending Migration
- Approved for Future Date
- Requires Research

## ES Fields Not in BBF (50+ fields)

ES Off_Net__c tracks significantly more vendor management details than BBF:

### Vendor Order Lifecycle (not in BBF)
- `Vendor_LOA_Date__c` (Letter of Authorization)
- `Vendor_ROE_Completed__c` (Right of Entry completion)
- `Vendor_ROE_Required__c` (ROE required flag)
- `FOC_Date__c` (Confirmed FOC date)
- `FOC_Date_Change_Count__c` (Number of FOC changes)
- `Requested_FOC_Date_Change__c` (FOC change requested)
- `Vendor_Rate_Increase_Notice_Received__c` (Rate increase tracking)
- `Vendor_Rate_Increase_Effective_Date__c`
- `Vendor_Rate_Increase_MRC__c`
- `Vendor_Bill_Stop_Date__c` (Billing stop date)

### ES Project and Personnel Tracking (not in BBF)
- `Project_Manager__c` (Project manager reference)
- `TechnicalContact__c` (Technical contact reference)
- `OSP_Engineer__c` (Outside plant engineer - likely moved to parent Service__c in BBF)

### ES Vendor Quote Management (not in BBF)
- `Selected_Off_Net_Vendor_Quote__c` (Selected quote reference)
- `Vendor_Quote_Notes__c` (Quote notes)

### ES Circuit and Network Details (not in BBF)
- `Bandwidth__c` (43-value picklist - BBF uses Product__c instead)
- `Circuit_Type__c` (12-value picklist - BBF uses Service_Type__c instead)
- `CFA__c` (Customer Furnished Access)
- `Ordering_CLLI__c`, `Serving_CLLI__c` (CLLI codes)
- `Facility_ID__c` (Facility identifier)

### ES Legacy/Migration Fields (not needed in BBF)
- `Old_Off_Net_Services_Record__c` (Old record reference)
- `Data_Load_ID__c`, `Data_Load_Source__c` (Migration tracking)
- `Implementation__c` (Deprecated - replaced by SOF1__c)
- `SOF__c`, `SOF_from_IMP__c` (Deprecated SOF references)

### ES Reporting/Rollup Fields (not in BBF)
- `Entity__c` (Formula field from related records)
- `LOC_Z_Address_SOF__c` (Formula field)
- `Circuit_Service_Id__c` (Formula field)
- `Service_Order_Agreement_Has_Successor__c` (Rollup)
- `Service_Order_Agreement_Status__c` (Rollup)
- `SOF_Account_Name__c`, `SOF_Related_Order_Portability__c`, `SOF_Order_Type__c` (Formula fields)

### ES Location Management (moved to Location__c in BBF)
- `Location_1__c`, `Location_2__c` (Location references - Day 1 migrated as AA_Location__c, ZZ_Location__c)
- `Location_1_Address__c`, `Location_2_Address__c` (Formula fields)

### ES Product and Summary Fields (not in BBF)
- `Product_Summary__c` (Product summary text)
- `Order_circuit_type__c`, `Order_cost_component_Id__c` (Order references)
- `Invoice_MRC__c` (Invoice MRC)

## Transformers Required (12 fields)

### Type Conversion Transformers (3)
1. **Aloc_COGS_Provider__c**: Reference → Text (extract vendor account name)
2. **Zloc_COGS_Provider__c**: Reference → Text (extract vendor account name)
3. **Vendor_NNI__c**: Reference → Text (extract NNI name)

### Picklist Value Mapping Transformers (2)
4. **Term__c**: ES → BBF term value mapping (handle "NO", "MO", 6, 18, 62)
5. **Off_Net_Service_Status__c**: Map "NOC Review" → "NOC Reiew" (or fix BBF typo)

### Text Truncation Transformers (2)
6. **BBF_Circuit_ID__c**: Truncate ES Internal_Circuit_Id__c (textarea 255 → string 100)
7. **Demarc_Location__c**: Truncate ES Demarc_Loaction__c (textarea 32768 → string 255)

### Complex Picklist Transformers (2)
8. **Product__c**: Map ES Bandwidth__c (43 values) → BBF Product__c (471 values)
   - **Business rules needed**: Bandwidth categories → Product catalog
9. **Service_Type__c**: Map ES Off_Net_Type__c (3 values) → BBF Service_Type__c (72 values)
   - **Business rules needed**: Circuit/Cross Connect/Collocation → detailed service types

### Data Quality Transformers (3)
10. **Off_Net_Problem_Reason_Code__c**: Validate values exist in both orgs (likely pass-through)
11. **Off_Net_Original_Due_Date__c**: Semantic validation (FOC date as original due date)
12. **Stripped_Circuit_ID__c**: Strip formatting from circuit IDs

## Business Review Required

### Priority 1 - Picklist Mappings
1. **Term__c**: How should ES "NO" and "MO" values map to BBF?
2. **Product__c**: What is the business rule for Bandwidth → Product mapping?
3. **Service_Type__c**: What is the business rule for Off_Net_Type → Service_Type mapping?

### Priority 2 - BBF-Only Fields
4. **Charge_Class__c**: Should this be derived from service type or left blank?
5. **Service_Order_Line__c**: Is this needed for ES migrations?

### Priority 3 - Vendor Provider Fields
6. Should A-Location and Z-Location COGS providers be populated separately in BBF?
7. How should vendor references be resolved (by name lookup)?

## Data Quality Considerations

### ES Data Issues Observed
1. **Typo in field name**: `Demarc_Loaction__c` (should be "Location")
2. **Deprecated fields**: Implementation__c, SOF__c still present in ES
3. **Multiple circuit ID fields**: Vendor_circuit_Id__c, Internal_Circuit_Id__c, Internal_Circuit_ID2__c

### BBF Data Issues Observed
1. **Typo in picklist value**: "NOC Reiew" should be "NOC Review"
2. **Product picklist size**: 471 values - may need consolidation

## Recommendations

### For Day 2 Migration
1. **High confidence fields**: Implement direct mappings with minimal validation
2. **Medium confidence fields**: Add validation to flag potential issues
3. **Low confidence fields**: Implement transformers with extensive business rule validation
4. **Vendor lookups**: Create name-based matching for vendor references
5. **Picklist mappings**: Get business approval before implementation

### For BBF Object Enhancement
1. Consider adding FOC tracking fields (FOC_Date__c, FOC_Date_Change_Count__c)
2. Consider adding rate increase tracking (valuable for vendor cost management)
3. Fix typo: "NOC Reiew" → "NOC Review"
4. Consider adding project personnel references if needed

### For Data Quality
1. Standardize circuit ID fields in ES before migration
2. Clean up deprecated fields in ES
3. Validate vendor references resolve correctly
4. Review large product picklist for consolidation opportunities

## Files Generated

- **Field Mapping**: `day-two/mappings/ES_Off_Net__c_to_BBF_Off_Net__c_mapping.xlsx`
  - Sheet 1: Field_Mapping (33 BBF fields)
  - Sheet 2: Picklist_Mapping (74 picklist value mappings)

- **Summary Document**: `day-two/mappings/ES_Off_Net__c_to_BBF_Off_Net__c_SUMMARY.md` (this file)

- **Export Metadata**:
  - `day-two/exports/es_Off_Net__c_fields_with_picklists.csv`
  - `day-two/exports/bbf_Off_Net__c_fields_with_picklists.csv`
  - `day-two/exports/es_Off_Net__c_picklist_values.csv`
  - `day-two/exports/bbf_Off_Net__c_picklist_values.csv`
  - `day-two/exports/off_net_mapping.json`

## Next Steps

1. **Business Review**: Share mapping with stakeholders for picklist decisions
2. **Transformer Development**: Build transformation scripts for 12 identified transformers
3. **Testing**: Validate mappings with POC data (6 Off_Net records)
4. **Enrichment**: Run Day 2 enrichment to populate all matched fields
5. **Validation**: Compare ES vs BBF data after enrichment for accuracy

---

**Mapping Generated**: 2026-01-15
**AI Matching Engine**: Semantic analysis with telecom off-net domain knowledge
**Status**: Ready for business review and transformer development

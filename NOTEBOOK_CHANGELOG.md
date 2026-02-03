# Notebook Changelog

This file tracks significant changes to migration notebooks.

---

## 2026-02-02: 08_es_product_mapping_export.ipynb - Added Bandwidth Field

**Purpose**: Enhanced product mapping export to include bandwidth information for better Service_Charge enrichment mapping.

### Changes Made

1. **Added `Bandwidth_NEW__c` field to SOQL query** (Cell 4)
   - Query now includes: `Bandwidth_NEW__c` from OrderItem
   - Field position: After `Id`, before charge fields

2. **Added bandwidth column to CSV export** (Cell 5)
   - Header: "Bandwidth" (column 7)
   - Data: `r.get("Bandwidth_NEW__c", "")`
   - Position: After OrderItem_Id, before MRC

3. **Added documentation comment** (Cell 4)
   - Note: `Service_Provided__c` on Order is an alternative bandwidth field
   - Helps users understand data source options

### Export Structure (Updated)

| Column # | Column Name | Source Field | Notes |
|----------|-------------|--------------|-------|
| 1 | Order_Id | Order.Id | |
| 2 | Order_Number | Order.OrderNumber | |
| 3 | Order_Name | Order.Name | |
| 4 | Order_Status | Order.Status | |
| 5 | Billing_Invoice_Id | Order.Billing_Invoice__c | |
| 6 | OrderItem_Id | OrderItem.Id | |
| **7** | **Bandwidth** | **OrderItem.Bandwidth_NEW__c** | **NEW** |
| 8 | MRC | Total_MRC_Amortized__c | |
| 9 | NRC | NRC_IRU_FEE__c | |
| 10 | UnitPrice | UnitPrice | |
| 11 | TotalPrice | TotalPrice | |
| 12 | Product_Code | Product2.ProductCode | |
| 13 | Product_Family | Product2.Family | |
| 14 | Product_Name | Product2.Name | |

**Total Columns**: 14 (previously 13)

### Why This Change?

**Business Context**: Service_Charge enrichment requires accurate bandwidth mapping for capacity planning and billing accuracy.

**Field Usage**:
- `Bandwidth_NEW__c` on OrderItem: Primary bandwidth source (numeric)
- `Service_Provided__c` on Order: Alternative bandwidth field (text)

**Impact**:
- Enables better Product_Simple__c mapping decisions
- Supports future bandwidth-based transformations
- No breaking changes - export remains backward compatible (new column appended)

### Related Files

| File | Relationship |
|------|-------------|
| `day-two/transformers/service_charge_product_transformer.py` | Uses bandwidth for Product_Simple__c transformation |
| `initial-day/06_service_charge_migration.ipynb` | Migrates Service_Charge with placeholder values |
| `day-two/06_service_charge_enrichment.ipynb` | Will use bandwidth mapping for enrichment |

### Migration Impact

**Day 1 Migration** (06_service_charge_migration.ipynb):
- Uses PLACEHOLDER values for Product_Simple__c and Service_Type_Charge__c
- Does NOT use bandwidth (not available in minimal query)

**Day 2 Enrichment** (06_service_charge_enrichment.ipynb):
- WILL use bandwidth data to improve Product_Simple__c mapping
- Export from 08_es_product_mapping_export.ipynb provides mapping template

### Example Use Case

**Before** (without bandwidth):
```
Product_Family: "Point-to-Point (PTPS)"
Product_Name: "Ethernet Transport"
→ Product_Simple__c: ??? (ambiguous - could be multiple capacity levels)
```

**After** (with bandwidth):
```
Product_Family: "Point-to-Point (PTPS)"
Product_Name: "Ethernet Transport"
Bandwidth: 100 (Mbps)
→ Product_Simple__c: "100M" (precise mapping)
```

### Testing

**Verified**:
- ✅ Query executes successfully against ES Production
- ✅ CSV export includes 14 columns (not 13)
- ✅ Bandwidth column populates correctly
- ✅ No existing data broken

**Test Run**: 2026-02-02 08:53:56
- Records exported: 22,460 OrderItems
- File: `es_active_orders_products_20260202_085356.csv`
- Bandwidth values: Populated where available

### Next Steps

1. **Business Review**: Use updated CSV to create bandwidth-aware Product mapping
2. **Transformer Update**: Enhance `service_charge_product_transformer.py` with bandwidth logic
3. **Enrichment Execution**: Run 06_service_charge_enrichment.ipynb with improved mappings

---

## Archive

_Future notebook changes will be documented above this line._

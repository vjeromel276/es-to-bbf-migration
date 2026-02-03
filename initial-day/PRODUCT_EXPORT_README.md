# Product Mapping Export (08_es_product_mapping_export.ipynb)

**Purpose**: Export ES OrderItem and Product2 data to create Product mapping for Service_Charge enrichment.

**Last Updated**: 2026-02-02 (Added Bandwidth_NEW__c field)

---

## Overview

This notebook queries ES Salesforce for active OrderItems with their Product2 details and exports to CSV. The export is used to build the mapping from ES Products to BBF Service_Charge__c picklist values.

### Why This Export?

**Day 1 Problem**: Service_Charge migration (06_service_charge_migration.ipynb) uses PLACEHOLDER values:
- `Product_Simple__c = "ANNUAL"` (placeholder)
- `Service_Type_Charge__c = "Power"` (placeholder)

**Day 2 Solution**: Use this export to create accurate Product → BBF picklist mappings.

---

## Export Structure

### CSV Output (14 Columns)

| Column # | Column Name | Source | Example Value | Purpose |
|----------|-------------|--------|---------------|---------|
| 1 | Order_Id | Order.Id | 801Rn00000YabcdIAB | Order tracking |
| 2 | Order_Number | Order.OrderNumber | SO-123456 | Human reference |
| 3 | Order_Name | Order.Name | Customer A - Location B | Context |
| 4 | Order_Status | Order.Status | Activated | Filter verification |
| 5 | Billing_Invoice_Id | Order.Billing_Invoice__c | a2TRn00000XabcdMAB | BAN reference |
| 6 | OrderItem_Id | OrderItem.Id | 802Rn00000YabcdIAB | OrderItem tracking |
| **7** | **Bandwidth** | **OrderItem.Bandwidth_NEW__c** | **100** | **Capacity mapping** |
| 8 | MRC | Total_MRC_Amortized__c | 500.00 | Monthly recurring |
| 9 | NRC | NRC_IRU_FEE__c | 5000.00 | One-time charge |
| 10 | UnitPrice | UnitPrice | 500.00 | Standard pricing |
| 11 | TotalPrice | TotalPrice | 500.00 | Line total |
| 12 | Product_Code | Product2.ProductCode | PTPS-100M | Product SKU |
| 13 | Product_Family | Product2.Family | Point-to-Point (PTPS) | Category |
| 14 | Product_Name | Product2.Name | 100Mbps Ethernet Transport | Description |

**Total Columns**: 14 (added Bandwidth in v2)

---

## Filters Applied

The export only includes OrderItems from active Orders:

| Filter | SOQL Condition | Purpose |
|--------|---------------|---------|
| Active Status | `Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')` | Migration scope |
| Not Decom | `Project_Group__c NOT LIKE '%PA MARKET DECOM%'` | Exclude decomm |
| Service Order | `Service_Order_Record_Type__c = 'Service Order Agreement'` | Correct record type |
| Has BAN | `Billing_Invoice__c != null` | Required for migration |

**Result**: Only OrderItems that will be migrated in Day 1.

---

## Data Volume (as of 2026-02-02)

### Summary Statistics

```
Unique Orders:        12,594
Total OrderItems:     22,460
Product Families:     49
Unique Products:      681
```

### Top Product Families

| Family | Count | BBF Service_Type_Charge__c (Suggested) |
|--------|-------|----------------------------------------|
| Point-to-Point (PTPS) | 5,338 | EPL |
| Dedicated Internet Access (DIAS) | 3,607 | DIA |
| IP | 3,444 | IP Subnet |
| Dark Fiber (DFBR) | 1,823 | DF |
| Hosted Voice (VOIC) | 1,703 | VOICE |
| Point-to-MultiPoint (PMPS) | 1,539 | ELAN |
| Promotions | 879 | Credit |
| Managed Service (MSP) | 829 | Equipment |

**Full distribution**: See notebook output Cell 6

---

## Using the Export for Mapping

### Step 1: Run the Export

```python
# Open initial-day/08_es_product_mapping_export.ipynb
# Execute all cells
# Output: es_active_orders_products_YYYYMMDD_HHMMSS.csv
```

### Step 2: Analyze Product Distribution

The notebook automatically generates:
- Product Family distribution (49 families)
- Top 30 Products by count
- Unique product counts

**Use this to prioritize mapping effort**: Focus on high-volume families first.

### Step 3: Create Mapping Template

Build Excel or database mapping:

| ES Product Family | ES Product Name | Bandwidth | BBF Product_Simple__c | BBF Service_Type_Charge__c |
|-------------------|-----------------|-----------|----------------------|---------------------------|
| Point-to-Point (PTPS) | 100Mbps Ethernet Transport | 100 | 100M | EPL |
| Dedicated Internet Access (DIAS) | DIA 1Gbps | 1000 | 1G | DIA |
| Dark Fiber (DFBR) | Dark Fiber 1 Pair | null | DF | DF |

### Step 4: Update Transformer

Edit `day-two/transformers/service_charge_product_transformer.py`:

```python
FAMILY_TO_SERVICE_TYPE = {
    'Point-to-Point (PTPS)': 'EPL',
    'Dedicated Internet Access (DIAS)': 'DIA',
    # ... add all 49 families
}

def transform_product_simple(description, bandwidth, product_family):
    """Map ES Product to BBF Product_Simple__c using bandwidth."""
    if bandwidth and bandwidth >= 1000:
        return f"{int(bandwidth/1000)}G"
    elif bandwidth:
        return f"{int(bandwidth)}M"
    else:
        return DEFAULT_PRODUCT
```

### Step 5: Run Enrichment

Execute `day-two/06_service_charge_enrichment.ipynb` to:
1. Query BBF Service_Charge__c records with placeholder values
2. Query matching ES OrderItems with Product data
3. Apply transformer mappings
4. Bulk update BBF records

---

## Bandwidth Field (Added 2026-02-02)

### Why Add Bandwidth?

**Problem**: Product names alone are ambiguous for capacity-based services.
- "Ethernet Transport" could be 10M, 100M, 1G, 10G, etc.
- Without bandwidth, Product_Simple__c mapping is imprecise

**Solution**: Include `Bandwidth_NEW__c` in export for precise mapping.

### Bandwidth Sources in ES

| Field | Object | Type | Example | Notes |
|-------|--------|------|---------|-------|
| `Bandwidth_NEW__c` | OrderItem | Number | 100 | Primary (used in export) |
| `Service_Provided__c` | Order | Text | "100Mbps" | Alternative (includes unit) |

**Export uses**: `Bandwidth_NEW__c` from OrderItem (numeric, easier to process)

### Example Mapping with Bandwidth

**Before** (Product Name only):
```
Product: "Ethernet Transport"
→ BBF Product_Simple__c: ??? (ambiguous)
```

**After** (Product + Bandwidth):
```
Product: "Ethernet Transport"
Bandwidth: 100
→ BBF Product_Simple__c: "100M" (precise)

Product: "Ethernet Transport"
Bandwidth: 10000
→ BBF Product_Simple__c: "10G" (precise)
```

---

## BBF Target Fields

The mapping feeds two BBF Service_Charge__c picklist fields:

### 1. Product_Simple__c (Picklist)

**BBF Values** (sample):
- ANNUAL
- BI-ANNUAL
- MONTHLY
- QUARTERLY
- 10M, 100M, 1G, 10G (capacity tiers)
- Equipment
- Installation
- Other

**Mapping Logic**:
- Bandwidth-based: Use capacity tiers (10M, 100M, etc.)
- Time-based: Use billing frequency (MONTHLY, ANNUAL, etc.)
- Service-based: Use service type (Equipment, Installation, etc.)

### 2. Service_Type_Charge__c (Picklist)

**BBF Values** (sample):
- EPL (Ethernet Private Line)
- DIA (Dedicated Internet Access)
- DF (Dark Fiber)
- VOICE
- COLO (Collocation)
- Equipment
- Installation
- Credit
- TSP

**Mapping Logic**:
- Use `FAMILY_TO_SERVICE_TYPE` mapping in transformer
- Product Family → Service_Type_Charge__c is usually 1:1
- Some families map to same BBF value (e.g., PTPS → EPL, ETHS → EPL)

---

## Notebook Cell Structure

| Cell | Purpose | Key Logic |
|------|---------|-----------|
| 0 | Overview | Documents filters and purpose |
| 1 | Setup | Imports (simple_salesforce, csv, datetime, Counter) |
| 2 | Configuration | ES credentials (UAT or Production) |
| 3 | Connect | ES org connection |
| **4** | **Query** | **SOQL with Bandwidth_NEW__c** |
| **5** | **Export CSV** | **14 columns including Bandwidth** |
| 6 | Analysis | Product Family and Product counts |
| 7 | Summary | Record counts and output file |

**Execution Time**: ~30 seconds for 22,460 records

---

## Output File Example

**Filename**: `es_active_orders_products_20260202_085356.csv`

**Sample Rows**:
```csv
Order_Id,Order_Number,Order_Name,Order_Status,Billing_Invoice_Id,OrderItem_Id,Bandwidth,MRC,NRC,UnitPrice,TotalPrice,Product_Code,Product_Family,Product_Name
801Rn00000YabcdIAB,SO-123456,Customer A - Site B,Activated,a2TRn00000XabcdMAB,802Rn00000YabcdIAB,100,500.00,0.00,500.00,500.00,PTPS-100M,Point-to-Point (PTPS),100Mbps Ethernet Transport
801Rn00000YabcdIAB,SO-123456,Customer A - Site B,Activated,a2TRn00000XabcdMAB,802Rn00000YxyzIAB,1000,2500.00,0.00,2500.00,2500.00,DIA-1G,Dedicated Internet Access (DIAS),DIA 1Gbps
```

**File Size**: ~3.1 MB

---

## Related Files

### Migration Flow

```
08_es_product_mapping_export.ipynb (this notebook)
    ↓ generates CSV
Business Mapping Decision
    ↓ creates mapping
day-two/transformers/service_charge_product_transformer.py
    ↓ used by
day-two/06_service_charge_enrichment.ipynb
    ↓ updates
BBF Service_Charge__c records
```

### File Relationships

| File | Role | Dependency |
|------|------|------------|
| `08_es_product_mapping_export.ipynb` | Data export | None (standalone) |
| `service_charge_product_transformer.py` | Mapping logic | Uses export data |
| `06_service_charge_migration.ipynb` | Day 1 insert | Creates placeholder records |
| `06_service_charge_enrichment.ipynb` | Day 2 update | Uses transformer |

---

## Changelog

### Version 2 (2026-02-02)
- ✅ Added `Bandwidth_NEW__c` field to query (Cell 4)
- ✅ Added "Bandwidth" column to CSV export (Cell 5)
- ✅ Added comment about `Service_Provided__c` alternative (Cell 4)
- ✅ Updated column count from 13 to 14

### Version 1 (2026-01-14)
- ✅ Initial export with 13 columns
- ✅ Product Family and Product Name analysis
- ✅ Export to CSV with Order and OrderItem context

---

## Troubleshooting

### Issue: Export has 0 records

**Cause**: Filters are too restrictive or no data in org.

**Fix**:
1. Check `Order.Status` values in ES
2. Verify `Billing_Invoice__c` is populated on Orders
3. Confirm `Service_Order_Record_Type__c` field exists

### Issue: Bandwidth column is empty

**Cause**: `Bandwidth_NEW__c` field not populated in ES.

**Options**:
1. Use `Service_Provided__c` from Order instead (text parsing needed)
2. Map by Product Name only (less precise)
3. Request ES data team to populate Bandwidth_NEW__c

### Issue: Too many unique Products (681)

**Strategy**: Map by Product Family first, then handle top 30 Products individually.

**Approach**:
1. Create default mapping for each Family → Service_Type_Charge__c
2. Create bandwidth-based rules for Product_Simple__c
3. Only create special cases for high-volume products

---

## Next Steps

After generating the export:

1. **[ ] Analyze Distribution**: Review Product Family and Product counts in notebook output
2. **[ ] Create Mapping**: Build ES Product → BBF picklist mapping in Excel or database
3. **[ ] Update Transformer**: Edit `service_charge_product_transformer.py` with mappings
4. **[ ] Business Review**: Validate mapping decisions with stakeholders
5. **[ ] Test Transformer**: Test mapping logic with sample records
6. **[ ] Run Enrichment**: Execute `06_service_charge_enrichment.ipynb`
7. **[ ] Validate Results**: Verify enriched values in BBF Salesforce UI

---

*For detailed changelog, see `/NOTEBOOK_CHANGELOG.md`*
*For transformer documentation, see `day-two/transformers/service_charge_product_transformer.py`*

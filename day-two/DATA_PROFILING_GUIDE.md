# ES Data Profiling Guide

**Purpose:** Analyze actual ES production data to inform field mapping decisions with real-world context.

**Created:** 2026-01-23
**Tool:** `day-two/tools/es_data_profiler.py`

---

## Why Data Profiling?

The AI-powered field mapping tools analyze **metadata** (field names, types, picklist options), but they don't see **actual data**. This creates gaps:

❌ **Without Data Profiling:**
- "This picklist has 20 values" → But you don't know which ones are actually used
- "This field exists" → But you don't know if it's 90% null or 90% populated
- "This string field is 255 chars" → But you don't know if data exceeds that limit
- "Map Field A to Field B" → But you don't know if Field A has any data

✅ **With Data Profiling:**
- "Payment_Terms__c: 80% use 'NET 30', 15% use 'NET 15', 5% use 'Prepaid', 12 other values are UNUSED"
- "Email: 95% populated (high value), Phone: 12% populated (low value)"
- "Description field: 45 records exceed 255 char limit, needs truncation"
- "Contact_Type__c: 'Decision Maker' used 1,200 times, 'Unknown' used 3 times"

---

## What the Profiler Analyzes

### 1. Field Population Rates
For every field, shows:
- Total records analyzed
- Number of populated records
- Number of null/empty records
- Population rate percentage
- Null rate percentage

**Use Case:** Prioritize mapping high-population fields, skip mostly-null fields

### 2. Picklist Value Distributions (ACTUAL USAGE)
For picklist/multipicklist fields, shows:
- Which values are actually used (with counts and percentages)
- Which metadata values are UNUSED (defined but never used)
- Which values are UNDEFINED (in data but not in metadata - data quality issue!)
- Top value combinations (for multipicklist)

**Use Case:**
- Focus transformers on values that actually exist
- Identify data quality issues
- Understand business patterns

### 3. String Field Length Analysis
For string/text fields, shows:
- Maximum length defined in metadata
- Actual maximum length found in data
- Actual minimum length
- Average length
- Number of records exceeding limit
- Whether truncation is needed

**Use Case:** Identify truncation requirements before migration

### 4. Numeric Field Range Analysis
For number/currency/percent fields, shows:
- Minimum value in dataset
- Maximum value in dataset
- Average value

**Use Case:** Understand data ranges for validation

### 5. Sample Records
Exports actual sample records for manual review

**Use Case:** Validate transformer logic with real data

---

## Output Files

For each object profiled, generates 4 CSV files:

### 1. `{Object}_field_population_summary_{timestamp}.csv`
**All fields** with population statistics

| Field Name | Field Label | Field Type | Population Rate % | Null Rate % |
|------------|-------------|------------|-------------------|-------------|
| Payment_Terms__c | Payment Terms | picklist | 87.5 | 12.5 |
| Description | Description | textarea | 23.4 | 76.6 |
| Custom_Field__c | Custom Field | string | 0.2 | 99.8 |

**Action:** Sort by Population Rate DESC to find high-value fields

### 2. `{Object}_picklist_distributions_{timestamp}.csv`
**Picklist fields only** with actual value usage

| Field Name | Picklist Value | Count | Percentage | Status |
|------------|----------------|-------|------------|--------|
| Payment_Terms__c | NET 30 | 4,523 | 80.2% | USED |
| Payment_Terms__c | NET 15 | 845 | 15.0% | USED |
| Payment_Terms__c | Prepaid | 271 | 4.8% | USED |
| Payment_Terms__c | NET 45 | 0 | 0% | UNUSED |
| Payment_Terms__c | COD | 0 | 0% | UNUSED |

**Action:**
- Build transformers ONLY for values in "USED" status
- Investigate "UNDEFINED" values (data quality issues)
- Ignore "UNUSED" values

### 3. `{Object}_field_recommendations_{timestamp}.csv`
**AI recommendations** on which fields to prioritize

| Field Name | Population Rate % | Recommendation | Reasoning |
|------------|-------------------|----------------|-----------|
| Email | 95.2 | PRIORITIZE | 95.2% populated - highly valuable field |
| Phone | 45.3 | CONSIDER | 45.3% populated - moderate value |
| Mobile | 8.1 | LOW PRIORITY | 8.1% populated - sparse data |
| Custom_Field__c | 0.2 | SKIP | 0.2% populated - mostly null |

**Action:** Focus Day Two enrichment on PRIORITIZE and CONSIDER fields

### 4. `{Object}_sample_records_{timestamp}.csv`
**Sample records** (first N records) for manual review

---

## Usage Examples

### Example 1: Profile Account object
```bash
cd /home/user/es-to-bbf-migration/day-two/tools

# Basic profiling with default 5,000 records
python es_data_profiler.py --object Account

# Profile with larger sample and include sample records
python es_data_profiler.py --object Account --sample-size 10000 --include-samples --sample-records 50
```

### Example 2: Profile Order object with BBF migration filter
```bash
# Profile ONLY Orders that meet BBF migration criteria
# (Active statuses + NOT PA MARKET DECOM)
python es_data_profiler.py --object Order --filter-bbf-orders --sample-size 10000
```

This ensures you analyze only the data that will actually be migrated!

### Example 3: Profile multiple objects at once
```bash
# Profile all key migration objects
python es_data_profiler.py --object Account Contact Order Address__c Billing_Invoice__c --sample-size 5000
```

### Example 4: Custom output directory
```bash
# Export to specific directory
python es_data_profiler.py --object Account --output-dir /path/to/custom/folder
```

---

## How to Use Profiling Data to Improve Field Mapping

### Step 1: Run Profiler Before AI Mapping

```bash
# Profile all 7 migration objects
python es_data_profiler.py --object Account Contact Address__c Billing_Invoice__c Order OrderItem Off_Net__c --sample-size 10000 --filter-bbf-orders
```

### Step 2: Review Field Recommendations

Open `{Object}_field_recommendations_{timestamp}.csv` and:
- Sort by Population Rate DESC
- Focus on fields marked "PRIORITIZE" and "CONSIDER"
- Skip fields marked "SKIP" (< 10% population)

### Step 3: Review Picklist Distributions

Open `{Object}_picklist_distributions_{timestamp}.csv` and:

**For transformer generation:**
- Build transformers ONLY for values with status "USED"
- Ignore "UNUSED" values (they're in metadata but never occur)

**For data quality:**
- Investigate "UNDEFINED" values (in data but not in metadata)
- These may indicate data corruption or old picklist values

### Step 4: Update AI Field Mappings

When running semantic field matching tools, you can now:

**Example: Account Payment Terms**

Before profiling:
```python
# Transformer maps all 20 possible values
PAYMENT_TERMS_MAP = {
    'NET 30': 'NET 30',
    'NET 15': 'NET 15',
    'NET 45': 'NET 45',  # ← NEVER USED!
    'NET 60': 'NET 60',  # ← NEVER USED!
    'COD': 'Cash on Delivery',  # ← NEVER USED!
    # ... 15 more unused values
}
```

After profiling:
```python
# Transformer maps only actually-used values (3 instead of 20!)
PAYMENT_TERMS_MAP = {
    'NET 30': 'NET 30',  # 80.2% of records
    'NET 15': 'NET 15',  # 15.0% of records
    'Prepaid': 'Prepaid',  # 4.8% of records
}
```

**Result:** Simpler, faster, more accurate transformers

### Step 5: Choose Better Source Fields

**Scenario:** BBF has a "Primary_Email__c" field. Which ES field should map to it?

Without profiling:
- "Email field exists, use that" (Guess)

With profiling:
```
Email: 95% populated
Personal_Email__c: 12% populated
Work_Email__c: 87% populated
```

**Decision:** Use Work_Email__c (87% populated) as primary source, with Email (95%) as fallback

---

## Integration with Existing Day-Two Tools

### Current Workflow (Metadata Only)
```
1. Export ES field metadata → es_export_sf_fields_with_picklists.py
2. Export BBF field metadata → bbf_export_sf_fields_with_picklists.py
3. Create mapping Excel → create_*_mapping.py
4. Generate transformers → generate_transformers.py
```

### Enhanced Workflow (Metadata + Data)
```
0. Profile ES actual data → es_data_profiler.py  ← NEW STEP
1. Export ES field metadata → es_export_sf_fields_with_picklists.py
2. Export BBF field metadata → bbf_export_sf_fields_with_picklists.py
3. Create mapping Excel (informed by profiling data) → create_*_mapping.py
4. Generate transformers (only for used values) → generate_transformers.py
```

---

## Recommended Profiling Approach

### Phase 1: Quick Profile (5K records each)
```bash
python es_data_profiler.py --object Account Contact Address__c Billing_Invoice__c --sample-size 5000
```

Review outputs, identify key fields.

### Phase 2: Deep Profile for Complex Objects (10K records)
```bash
# Profile Order with BBF filter
python es_data_profiler.py --object Order --filter-bbf-orders --sample-size 10000 --include-samples

# Profile OrderItem (linked to filtered Orders)
python es_data_profiler.py --object OrderItem --sample-size 10000
```

### Phase 3: Full Production Profile (50K+ records)
```bash
# For critical objects, analyze larger sample
python es_data_profiler.py --object Account Order --sample-size 50000 --filter-bbf-orders
```

---

## Performance Considerations

**Query Performance:**
- 5,000 records: ~30-60 seconds per object
- 10,000 records: ~60-120 seconds per object
- 50,000 records: ~5-10 minutes per object

**Recommendations:**
- Start with 5K sample for initial exploration
- Use 10K sample for production mapping decisions
- Use 50K+ sample only for critical validation

**Salesforce API Limits:**
- Each profile run = 1 SOQL query per object
- Safe to profile all 7 objects in single session
- No risk of hitting daily API limits

---

## Troubleshooting

### Error: "INVALID_FIELD: No such column"
**Cause:** Field exists in metadata but not in database (never created in org)

**Solution:** Field will be skipped automatically, check logs

### Error: "MALFORMED_QUERY"
**Cause:** Special characters in field names or query syntax

**Solution:** Check SOQL query in output, may need to escape field names

### Warning: "Undefined picklist values found"
**Cause:** Data contains values not in current picklist metadata

**Explanation:** This is a **data quality issue** - values were entered before picklist was restricted, or old values were deactivated but data remains.

**Action:**
1. Document in migration notes
2. Decide if values should be migrated as-is or normalized
3. May need business stakeholder review

---

## Next Steps After Profiling

1. **Review all 4 output files** for each object
2. **Update field mapping Excel files** with profiling insights
3. **Regenerate transformers** (only for actually-used values)
4. **Document data quality issues** (undefined values, truncation needs)
5. **Share picklist distributions** with business stakeholders for validation
6. **Prioritize Day Two enrichment** based on field recommendations

---

## Questions This Answers

✅ "Which picklist values are actually used in production?"
✅ "Is this field worth mapping? (population rate)"
✅ "Will data fit in the target field? (length analysis)"
✅ "Which ES field has the most data for this BBF field?"
✅ "Are there data quality issues to fix before migration?"
✅ "What are the most common values for this field?"
✅ "Should I build a transformer for this value that appears 0 times?"

---

## Example Output Insights

### Real-World Example: Order Object Profiling

**Finding 1: Payment Terms**
```
Payment_Terms__c (87% populated)
- 'NET 30': 4,523 records (80.2%)  ← Build transformer
- 'NET 15': 845 records (15.0%)    ← Build transformer
- 'Prepaid': 271 records (4.8%)    ← Build transformer
- 'NET 45': 0 records (0%)         ← SKIP (never used)
- 'NET 60': 0 records (0%)         ← SKIP (never used)
- 'COD': 0 records (0%)            ← SKIP (never used)
```

**Action:** Build simple 3-value transformer instead of 20-value transformer

**Finding 2: Custom Fields**
```
Legacy_System_ID__c: 0.1% populated → SKIP
Order_Notes__c: 95% populated → PRIORITIZE
Custom_Field_123__c: 0% populated → SKIP
```

**Action:** Don't waste time mapping fields with 0% data

**Finding 3: String Truncation**
```
Description field:
- Max length defined: 255 chars
- Actual max length: 487 chars
- Records exceeding limit: 45
- Truncation needed: YES
```

**Action:** Add truncation logic to transformer before migration fails

---

## Summary

**The data profiler bridges the gap between metadata analysis and reality.**

It answers: "What does the actual data look like?" not just "What could the data look like?"

Use it BEFORE creating field mappings to make data-driven decisions instead of metadata-driven guesses.

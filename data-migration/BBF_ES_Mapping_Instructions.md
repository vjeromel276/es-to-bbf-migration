# BBF to ES Field Mapping Workbook - User Guide

## Overview

This workbook is designed to map Bluebird Fiber (BBF) Salesforce fields to their corresponding EverStream (ES) Salesforce fields. Since BBF is the target system after acquiring ES, this mapping will help identify where data should come from in the ES org to populate BBF fields.

**Important:** This is NOT a 1-to-1 migration. BBF fields may be populated from different ES objects entirely (e.g., a BBF Service_Order__c field might come from ES Opportunity).

---

## Workbook Structure

### Each Tab = One BBF Object
- 25 tabs total (one per BBF object)
- Each tab contains all fields for that object

### Column Definitions

| Column | Purpose | Who Fills It |
|--------|---------|--------------|
| **A: BBF Field Label** | User-friendly field name in BBF | Pre-filled |
| **B: BBF Field API Name** | Technical field name in BBF | Pre-filled |
| **C: BBF Field Type** | Data type (text, number, picklist, etc.) | Pre-filled |
| **D: Required** | "Yes" if field is required, "No" if optional | Pre-filled |
| **E: BBF Picklist Values** | Active picklist values (semicolon-separated) | Pre-filled |
| **F: Description** | Business description of what this field stores | **BBF Team** |
| **G: ES Source Object** | Which ES object contains the source data | **ES Team** |
| **H: ES Source Field** | Which ES field maps to this BBF field | **ES Team** |
| **I: ES Picklist Values** | ES picklist values if applicable | **ES Team** |
| **J: Transformation Notes** | Any logic needed to transform ES → BBF | **Both Teams** |

---

## Instructions for BBF Team

### Your Responsibilities

You are responsible for **Column F: Description**

For each field in each object tab:
1. Write a clear business description of what data this field contains
2. Explain when/how this field is used in your business process
3. Note any business rules or validations
4. Indicate if the field is critical for your operations

### Tips for Writing Descriptions

**Good Examples:**
- ✅ "Customer's preferred billing frequency (Monthly, Quarterly, Annual). Used for invoice generation."
- ✅ "Installation completion date. Required before service can go live. Must be after Order Date."
- ✅ "Primary contact for technical escalations. Should have phone and email populated."

**Avoid:**
- ❌ "The name" (too vague)
- ❌ "Date field" (restates the obvious)
- ❌ Leaving blank

### Required Fields (Yellow Highlighted)

Fields highlighted in **yellow** are REQUIRED in BBF. These are your highest priority:
- Must have a data source identified
- Must have transformation logic documented if needed
- Cannot be left blank during data load

### Process Recommendations

1. **Start with critical objects:** Account, Contact, Service_Order__c, Opportunity
2. **Work by business process:** Complete all fields for one object before moving to next
3. **Ask questions:** If you're unsure about a field's purpose, consult your business analysts
4. **Be specific:** The more detail you provide, the easier mapping will be

---

## Instructions for ES Team

### Your Responsibilities

You are responsible for **Columns G, H, and I**:
- **Column G:** ES Source Object
- **Column H:** ES Source Field  
- **Column I:** ES Picklist Values (if the field is a picklist)

### How to Complete the Mapping

#### Step 1: Read the BBF Description
- Review Column F to understand what data is needed
- Consider the BBF field type and picklist values

#### Step 2: Identify Source Object
In **Column G**, write the ES object API name where the data exists:
- Exact match? Use the same object (e.g., Account → Account)
- Different structure? Note the actual source (e.g., BBF Service_Order__c might come from ES Order OR Opportunity)

**Common ES Objects:**
- Account
- Contact
- Lead
- Opportunity
- Order
- OrderItem
- Product2
- SBQQ__Quote__c (CPQ Quotes)
- SBQQ__QuoteLine__c (CPQ Quote Lines)
- Billing_Invoice__c
- Address__c

#### Step 3: Identify Source Field
In **Column H**, write the ES field API name:
- Use exact field API names from your org
- For standard fields, these are pre-populated where they match
- For custom fields, you'll need to identify them

**Examples:**
```
BBF Field: Service_Start_Date__c
ES Source Object: Order
ES Source Field: ActivatedDate

BBF Field: Primary_Contact__c
ES Source Object: Account
ES Source Field: Primary_Contact__c

BBF Field: Installation_Address__c
ES Source Object: Address__c
ES Source Field: Full_Address__c
```

#### Step 4: Document Picklist Values (If Applicable)
If the BBF field is a picklist:
1. Check **Column E** to see BBF's active values
2. In **Column I**, list the ES picklist values (semicolon-separated)
3. Note any value differences

**Example:**
```
BBF Picklist Values (Column E): Active; Inactive; Pending; Closed
ES Picklist Values (Column I): Open; Closed; On Hold; Cancelled

Note: Will need transformation logic in Column J
```

#### Step 5: Handle Special Cases

**Case 1: Data Comes from Multiple ES Fields**
```
ES Source Object: Order
ES Source Field: Street + City + State + PostalCode
Transformation Notes: Concatenate address fields with proper formatting
```

**Case 2: Data Comes from Related Object**
```
ES Source Object: Opportunity.Account
ES Source Field: Industry
Transformation Notes: Get from parent Account record
```

**Case 3: No Direct Source Exists**
```
ES Source Object: [NONE]
ES Source Field: [NONE]
Transformation Notes: Need to derive from business logic or set default value
```

**Case 4: Different Object Architecture**
```
BBF Object: Service_Order__c
ES Source Object: Order OR Opportunity (depends on record type)
ES Source Field: Various - see transformation notes
Transformation Notes: New BBF Service_Orders come from ES Opportunities. Existing active services come from ES Orders.
```

### Pre-Populated Fields

Standard fields that match exactly between ES and BBF are **already filled in** for you:
- Common fields like: Name, Description, CreatedDate, etc.
- These appear in Columns G and H
- **Still review them** to confirm they're correct

### Tips for ES Team

1. **Use SOQL to verify:** Query your ES org to confirm field API names
2. **Check field types:** Make sure data types are compatible
3. **Consider relationships:** Note if you need to traverse relationships (e.g., Order → Account → Name)
4. **Document lookups:** If the BBF field is a lookup, note the relationship
5. **Test complex logic:** For fields requiring transformation, write pseudo-code in Column J

---

## Instructions for Both Teams - Column J: Transformation Notes

This column is for **any logic needed** to convert ES data to BBF format.

### When to Use Transformation Notes

1. **Picklist value translation**
   ```
   ES "Active" → BBF "Active"
   ES "Inactive" → BBF "Closed"
   ES "Pending" → BBF "Pending Review"
   ```

2. **Data type conversions**
   ```
   ES Text(100) → BBF Text(50): Truncate if needed
   ```

3. **Calculation or formula**
   ```
   BBF Monthly_Revenue__c = ES Annual_Revenue__c / 12
   ```

4. **Concatenation**
   ```
   BBF Full_Name__c = ES FirstName + " " + LastName
   ```

5. **Conditional logic**
   ```
   IF ES.Order.Type = "New" THEN BBF.Service_Order__c.Category__c = "New Installation"
   ELSE IF ES.Order.Type = "Upgrade" THEN BBF.Service_Order__c.Category__c = "Service Upgrade"
   ```

6. **Default values**
   ```
   If ES field is blank, use default: "Standard"
   ```

7. **Date formatting**
   ```
   Convert ES date format to BBF timezone
   ```

### Transformation Note Best Practices

- Be specific and technical
- Use pseudo-code or plain English
- Note any business rules
- Flag any potential data quality issues
- Indicate if manual review is needed

---

## Working Process Recommendations

### Phase 1: Initial Review (Week 1)
1. **BBF Team:** Complete descriptions for all required fields (yellow highlighted)
2. **ES Team:** Map all standard fields and simple matches
3. **Both:** Review progress together, identify questions

### Phase 2: Complex Mappings (Week 2)
1. **BBF Team:** Complete remaining descriptions
2. **ES Team:** Map custom fields and complex scenarios
3. **Both:** Document transformation logic for critical fields

### Phase 3: Review & Validation (Week 3)
1. **Joint session:** Review all mappings together
2. **Identify gaps:** Find unmapped required fields
3. **Document decisions:** For fields with no source, determine solution
4. **Prioritize:** Mark critical vs. nice-to-have fields

### Phase 4: Testing Prep (Week 4)
1. Create transformation scripts based on Column J notes
2. Test mappings with sample data
3. Validate picklist value translations
4. Document any exceptions or manual processes needed

---

## Key Objects to Prioritize

Based on business criticality, focus on these objects first:

### Tier 1 (Critical - Start Here)
1. **Account** - Customer master data
2. **Contact** - Customer contacts
3. **Service_Order__c** - Core service orders
4. **Opportunity** - Sales pipeline

### Tier 2 (High Priority)
5. **Product2** - Product catalog
6. **Service_Order_Line__c** - Service order line items
7. **Quote** - Customer quotes
8. **Service__c** - Active services

### Tier 3 (Medium Priority)
9. **Lead** - Marketing/sales leads
10. **BAN__c** - Billing account numbers
11. **Location__c** - Service locations

### Tier 4 (Complete as Time Allows)
12. All remaining objects

---

## Common Questions

**Q: What if a BBF field has no equivalent in ES?**
A: Note "[NONE]" in Columns G and H. In Column J, document if this should be:
- Left blank
- Set to a default value
- Derived from business logic
- Populated manually post-migration

**Q: What if BBF picklist values don't match ES values?**
A: Document the translation in Column J. Example: "ES 'Open' → BBF 'Active'"

**Q: What if one BBF field needs data from multiple ES fields?**
A: List all source fields in Column H (separated by +), and explain the logic in Column J.

**Q: What if the data structure is completely different?**
A: Use Column J extensively. Document the logic, consider creating a separate mapping document, and flag for technical review.

**Q: Can I leave fields blank if I don't know?**
A: For now, yes - but mark them with "???" in Column J so we can follow up. Required fields MUST be resolved before migration.

**Q: Should I map deprecated or unused fields?**
A: Focus on active fields first. If a BBF field is deprecated/unused, note "DEPRECATED - DO NOT MAP" in Column F.

---

## Tips for Success

### For Everyone:
- ✅ Be thorough but practical
- ✅ Ask questions early and often  
- ✅ Focus on required fields first
- ✅ Document your assumptions
- ✅ Use consistent terminology
- ✅ Review each other's work

### Red Flags to Watch For:
- ⚠️ Required BBF fields with no source
- ⚠️ Data type mismatches (e.g., Text → Number)
- ⚠️ Picklist values that don't translate
- ⚠️ Complex transformations that might lose data
- ⚠️ Fields that require manual intervention at scale

---

## Support

**Questions about the workbook or process:**
- Contact the migration project team
- Schedule mapping review sessions
- Document complex scenarios for group discussion

**Technical questions about ES fields:**
- Query your Salesforce org
- Review ES documentation
- Consult ES administrators

**Business questions about BBF fields:**
- Consult BBF process documentation
- Review with business analysts
- Check with BBF administrators

---

## Workbook Statistics

- **Total Objects:** 25 BBF objects
- **Total Fields:** 2,071 unique fields
- **Fields by Object:** Ranges from 11 to 284 fields per object
- **Required Fields:** Highlighted in yellow
- **Picklist Fields:** Values shown in Column E where applicable

---

## Next Steps After Completion

Once the workbook is complete:
1. **Data validation:** Test mappings with sample data
2. **Script development:** Build transformation code based on Column J
3. **Gap remediation:** Create missing fields in BBF if needed
4. **Volume assessment:** Determine data volumes for migration planning
5. **Migration execution:** Load data based on validated mappings

---

**Version:** 1.0  
**Created:** November 20, 2025  
**Project:** EverStream to Bluebird Fiber Migration  
**Purpose:** Field-level mapping from ES (source) to BBF (target)

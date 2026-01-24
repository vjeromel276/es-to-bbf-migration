# Email: ES to BBF Migration Package

---

**Subject:** ES to BBF Salesforce Migration Scripts Package

---

Hi,

Attached is `migration-package.zip` containing the scripts and notebooks for the ES to BBF Salesforce data migration.

## What This Package Contains

### Initial Day Migration (initial-day/)
Seven Jupyter notebooks that migrate required fields from ES to BBF in dependency order:

1. **Location** - ES Address__c → BBF Location__c
2. **Account** - ES Account → BBF Account
3. **Contact** - ES Contact → BBF Contact (requires Account)
4. **BAN** - ES Billing_Invoice__c → BBF BAN__c (requires Account)
5. **Service** - ES Order → BBF Service__c (requires BAN - master-detail)
6. **Service Charge** - ES OrderItem → BBF Service_Charge__c (requires Service - master-detail)
7. **Off-Net** - ES Off_Net__c → BBF Off_Net__c (requires Service - optional lookup)

These notebooks handle the "Day One" migration of required fields only, with built-in filtering to ensure only actively billing orders are migrated (excluding PA MARKET DECOM).

### Day Two Field Mapping & Enrichment (day-two/)
Python scripts and tools for the "Day Two" enrichment phase:

- **tools/** - Scripts to export Salesforce metadata, create field mappings with AI semantic matching, and generate transformer functions
- **transformers/** - Auto-generated Python functions that convert ES field values to BBF-compatible formats (81 functions across 7 objects)
- **README.md** - Detailed documentation of the field mapping process and results

## What You Need to Do

1. **Add your Salesforce credentials** to the scripts (search for placeholders like `ES_USERNAME`, `BBF_USERNAME`, etc.)
2. **Run the export scripts** to pull fresh metadata from both orgs
3. **Review the generated mappings** and make business decisions on picklist values
4. **Execute the notebooks** in order, starting with Location

See the included `PACKAGE_README.md` for step-by-step setup instructions.

## Key Migration Rules

- Only actively billing orders: Status = Activated, Suspended, or Disconnect in Progress
- Excludes all PA MARKET DECOM orders
- Uses ES_Legacy_ID__c to track migrated records in BBF
- Uses BBF_New_Id__c to store new BBF IDs on ES records

Let me know if you have any questions.

---

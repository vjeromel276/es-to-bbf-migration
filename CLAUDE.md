# CLAUDE.md - Project Instructions

## Primary Directive

**AT THE START OF EVERY NEW CHAT READ THE PRIOR DAYS COMMIT NOTES. CHECK CODE, METADATA, WHATEVER YOU NEED SO THAT WE DON'T HAVE TO TAKE TIME TO FIX IT LATER ON.**

Before writing any migration code:
1. Export and read the actual BBF object metadata (field names, types, required fields)
2. Verify field names are EXACT - case sensitive (e.g., `mrc__c` not `MRC__c`)
3. Check if fields exist before using them
4. Identify which fields are truly REQUIRED (Is Nillable = False) vs optional
5. Check if Name fields are autonumber (don't set them)
6. Check if OwnerId exists on the object (not all custom objects have it)

## Project Context

ES to BBF Salesforce Data Migration - migrating data from EverStream (ES) Salesforce org to BlueBird Fiber (BBF) Salesforce org.

### Migration Order (Dependencies)
1. Location__c (no dependencies)
2. Account (no dependencies)
3. Contact (depends on Account)
4. BAN__c (depends on Account)
5. Service__c (depends on BAN__c - master-detail)
6. Service_Charge__c (depends on Service__c - master-detail)
7. Off_Net__c (depends on Service__c - optional lookup)

### Key Rules
- Only migrate actively billing orders (Status = Activated, Suspended, Disconnect in Progress)
- EXCLUDE all PA MARKET DECOM orders (Project_Group__c NOT LIKE '%PA MARKET DECOM%')
- Day 1 = Required fields only, Day 2+ = Enrichment
- Boolean fields default to False in Salesforce - don't need to set them
- Use ES_Legacy_ID__c to track migrated records in BBF
- Use BBF_New_Id__c to store new BBF IDs on ES records

### Field Metadata Files
Export BBF metadata before making changes:
- `Service__c_fields.csv`
- `Service_Charge__c_fields.csv`
- `Off_Net__c_fields.csv`
- `BAN__c_fields.csv`

### Notebooks Location
All migration notebooks are in `initial-day/` directory.

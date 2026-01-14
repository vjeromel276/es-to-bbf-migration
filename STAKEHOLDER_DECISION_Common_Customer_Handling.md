# STAKEHOLDER DECISION DOCUMENT
## Common Customer Handling Strategy
### ES to BBF Salesforce Data Migration

---

**Document Owner:** Migration Project Manager
**Date Created:** 2026-01-14
**Status:** PENDING DECISION
**Priority:** HIGH - Blocking migration completion

---

## EXECUTIVE SUMMARY

During the EverStream (ES) to Bluebird Fiber (BBF) Salesforce data migration, we have identified customers that exist in **BOTH** the ES Salesforce org **AND** the BBF Salesforce org. BBF's duplicate detection rules are blocking Account creation for these records during migration.

**This decision is required to proceed with:**
- BAN__c migration (Billing Account Numbers)
- Service__c migration (Orders/Circuits)
- Service_Charge__c migration (Line items)

**This document presents four strategic options and requires stakeholder approval to proceed.**

---

## BACKGROUND

### What Are "Common Customers"?

Common customers are organizations that:
1. Have an Account record in the BBF Salesforce org (existing BBF customer)
2. Also have an Account record in the ES Salesforce org (ES customer being migrated)
3. Represent the same real-world business entity

### Discovery Details

- **Source:** BBF's duplicate detection rules triggered during trial migration runs
- **Detection Method:** BBF has configured duplicate rules based on Account matching criteria
- **Current Status:** These Account creation attempts are being blocked by BBF Salesforce

### Why This Matters

While we cannot (and should not) create duplicate Account records, we **must** migrate the ES customer's operational data:
- **BAN__c records** (Billing Account Numbers) - Required for Service__c creation
- **Service__c records** (Active circuits/orders) - Core business data
- **Service_Charge__c records** (MRC/NRC charges) - Billing information
- **Contact records** - Customer contacts from ES system

**Without a decision on how to handle common customers, we cannot complete the migration of their operational data.**

---

## OPTION ANALYSIS

### Option 1: Link to Existing BBF Account (RECOMMENDED)

**Description:**
Use a matching strategy to identify the existing BBF Account and link ES operational data (BANs, Services) to that existing Account.

**Process Flow:**
1. Pre-migration: Export BBF Accounts with matching keys (EIN, Account Name, etc.)
2. During migration: When ES Account is identified as "common customer":
   - Look up existing BBF Account ID using matching key
   - Use that BBF Account ID when creating BAN__c and Service__c records
   - Update ES Account with `BBF_New_Id__c` to point to existing BBF Account
3. Result: All ES services properly associated with existing BBF Account

**Matching Key Options:**
- **Option 1A:** EIN (Tax ID) - Most reliable if available and accurate
- **Option 1B:** Account Name + State - Requires data normalization
- **Option 1C:** External ID field (if BBF and ES share common identifier)
- **Option 1D:** Manual mapping file provided by business team

**PROS:**
- Clean data model - no duplicate Accounts
- All services properly associated with correct customer
- Maintains data integrity
- BBF users see complete customer picture (BBF + ES services)
- Aligns with long-term consolidated data strategy

**CONS:**
- Requires reliable matching key (data quality dependent)
- Risk of incorrect matches if matching key is unreliable
- May require data cleansing before migration
- Additional development effort for matching logic

**RISKS:**
- **MEDIUM:** Incorrect matches could associate ES services with wrong BBF Account
- **LOW:** Missing matching keys could leave some records unmatched
- **MITIGATION:** Generate pre-migration matching report for business review

---

### Option 2: Skip Common Customers Entirely

**Description:**
Do not migrate any data (BANs, Services, Contacts) for customers that already exist in BBF.

**Process Flow:**
1. During migration: When ES Account is identified as "common customer":
   - Log the Account as "skipped - common customer"
   - Do not create BAN__c, Service__c, or Service_Charge__c records
   - Do not migrate Contacts
2. Result: Only ES-unique customers are migrated

**PROS:**
- Simple implementation - no matching logic required
- Zero risk of duplicate Accounts
- Zero risk of incorrect associations

**CONS:**
- **CRITICAL:** ES services for common customers will NOT be in BBF
- Incomplete migration - potentially thousands of active circuits not migrated
- BBF billing team will not see ES services for these customers
- May violate migration requirements for "all active billing services"

**RISKS:**
- **HIGH:** Business continuity issues if ES services are not in BBF
- **HIGH:** Revenue recognition issues if billing data is incomplete
- **CRITICAL:** May not meet Day 1 operational requirements

**IMPACT QUESTIONS:**
- How many customers are affected?
- What percentage of ES revenue do they represent?
- Can BBF operate without this data in Salesforce?

---

### Option 3: Manual Review Queue

**Description:**
Flag common customers for human review. Business analyst or data steward reviews each case and manually decides how to handle.

**Process Flow:**
1. Pre-migration: Generate list of all common customers
2. Business team reviews each customer and provides decision:
   - Link to specific BBF Account ID (provide mapping)
   - Skip this customer
   - Create new Account with modified name
3. Migration uses manual decision file to process each customer

**PROS:**
- Highest accuracy - human judgment on each case
- Handles edge cases and complex scenarios
- No risk of automated incorrect matches
- Business team maintains full control

**CONS:**
- **CRITICAL:** Time-consuming - may delay migration significantly
- Does not scale well (dozens or hundreds of customers?)
- Requires dedicated business resources
- Creates bottleneck in migration timeline

**RISKS:**
- **HIGH:** Timeline delay - manual review could take days/weeks
- **MEDIUM:** Inconsistent decisions across different reviewers
- **LOW:** Human error in providing Account ID mappings

**RESOURCE QUESTIONS:**
- Who would perform the review? (Names, roles)
- What is the expected volume of common customers?
- How long would review process take?
- Is this within Day 1 timeline constraints?

---

### Option 4: Create Separate "ES Legacy" Account

**Description:**
Create a new Account with a distinguishing marker (e.g., "Acme Corp - ES Legacy") to differentiate from existing BBF Account.

**Process Flow:**
1. During migration: When ES Account is identified as "common customer":
   - Modify Account Name to add " - ES Legacy" suffix
   - Create new Account in BBF with modified name
   - Create BAN__c and Service__c records linked to this new Account
2. Post-migration: Business team merges duplicate Accounts later

**PROS:**
- All data migrated - no data loss
- Clear separation between ES and BBF legacy data
- Simple implementation - no matching logic required
- Can proceed immediately

**CONS:**
- **CRITICAL:** Creates true duplicate Accounts in BBF
- Requires future cleanup/merge effort (post Day 1)
- BBF users see two Accounts for same customer
- Merge process may be complex (Services, BANs, Contacts all need reassignment)
- May violate BBF data quality standards

**RISKS:**
- **HIGH:** Duplicate Accounts cause confusion for sales/service teams
- **MEDIUM:** Merge effort could be substantial (weeks of work)
- **LOW:** Some users may not realize they need to check both Accounts

**CLEANUP QUESTIONS:**
- Who would perform post-migration merge?
- What is acceptable timeline for cleanup?
- Is this approach acceptable to BBF leadership?

---

## DECISION MATRIX

| Criteria | Option 1: Link to Existing | Option 2: Skip Customers | Option 3: Manual Review | Option 4: ES Legacy Account |
|----------|---------------------------|--------------------------|------------------------|----------------------------|
| **Data Completeness** | Complete | Incomplete | Complete | Complete |
| **Data Quality** | High (if matching is accurate) | N/A | Highest | Low (duplicates) |
| **Implementation Complexity** | Medium | Low | Low | Low |
| **Timeline Impact** | +1-2 days | None | +1-2 weeks | None |
| **Resource Requirements** | Development | None | Heavy business team | None |
| **Scalability** | High | High | Low | High |
| **Risk of Errors** | Medium | Low | Low | Low |
| **Post-Migration Cleanup** | None | N/A | None | High (weeks) |
| **Business Continuity** | Full | Impaired | Full | Full |
| **Long-term Maintainability** | Excellent | N/A | Excellent | Poor |

---

## RECOMMENDATION

**The migration team recommends Option 1: Link to Existing BBF Account**

**Rationale:**
1. Ensures complete data migration (all active services in BBF)
2. Maintains data quality (no duplicates)
3. Aligns with long-term consolidated data strategy
4. Reasonable timeline impact (1-2 days for matching logic)
5. No post-migration cleanup required

**Recommended Matching Strategy:**

**Primary Matching Key:** EIN (Tax ID)
- Most reliable unique identifier
- Already exists in both orgs (if populated)

**Fallback Matching:** Manual mapping file
- For records where EIN is missing or unreliable
- Business team provides ES Account ID → BBF Account ID mapping
- Estimated volume: TBD (requires analysis)

**Validation Process:**
1. Generate pre-migration matching report showing proposed links
2. Business team reviews report (focus on high-value customers)
3. Business team provides corrections/overrides if needed
4. Execute migration with approved matching logic

---

## INFORMATION NEEDED FOR DECISION

To evaluate and implement any option, stakeholders must provide:

### Data Analysis Needed
- [ ] How many common customers exist? (Run duplicate detection analysis)
- [ ] What percentage of ES Accounts are common customers?
- [ ] What percentage of ES Services belong to common customers?
- [ ] What is the revenue impact of common customers?

### Matching Key Analysis (if Option 1 selected)
- [ ] EIN field population rate in ES Accounts
- [ ] EIN field population rate in BBF Accounts
- [ ] EIN data quality assessment (duplicates, invalid values)
- [ ] Alternative matching fields available (if EIN not viable)

### Resource Availability (if Option 3 selected)
- [ ] Who can perform manual review?
- [ ] How many hours/days can they dedicate?
- [ ] What is their availability relative to Day 1 timeline?

### Business Policy (if Option 4 selected)
- [ ] Is creating duplicate Accounts acceptable to BBF leadership?
- [ ] Who would perform post-migration merge?
- [ ] What is acceptable timeline for merge completion?

---

## IMPACT OF DELAY

**CRITICAL: This decision is blocking migration completion.**

### Directly Blocked
- BAN__c migration for common customers
- Service__c migration for common customers
- Service_Charge__c migration for common customers
- Contact migration for common customers

### Timeline Impact
- Each day of delay pushes Day 1 readiness date
- Sale close date may not align with migration readiness
- May require expedited testing if decision is delayed

### Business Impact
- Cannot provide accurate "go-live" date to business stakeholders
- Cannot complete UAT testing until decision is made
- Risk of incomplete migration if decision is made too close to Day 1

---

## DECISION RECORD

### Decision

**Selected Option:** ________________________________________

**Matching Key (if Option 1):** ________________________________________

**Justification:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Stakeholder Sign-Off

| Name | Role | Approval | Date |
|------|------|----------|------|
| ________________________ | BBF Salesforce Lead | ☐ Approved ☐ Rejected | __________ |
| ________________________ | ES Migration Lead | ☐ Approved ☐ Rejected | __________ |
| ________________________ | Business Sponsor | ☐ Approved ☐ Rejected | __________ |
| ________________________ | Data Governance | ☐ Approved ☐ Rejected | __________ |

### Action Items (Post-Decision)

- [ ] Notify migration team of decision
- [ ] Update migration notebooks to implement chosen strategy
- [ ] Update migration documentation with decision and rationale
- [ ] Communicate decision to broader stakeholder group
- [ ] Schedule follow-up meeting if additional analysis is required

---

## APPENDIX A: ANALYSIS QUERIES

### To Identify Common Customer Count

Run this analysis in both orgs to estimate impact:

**BBF Org Query:**
```sql
SELECT COUNT(Id), COUNT(DISTINCT Tax_ID__c)
FROM Account
WHERE Tax_ID__c != NULL
```

**ES Org Query:**
```sql
SELECT COUNT(Id), COUNT(DISTINCT Tax_ID__c)
FROM Account
WHERE Tax_ID__c != NULL
  AND BBF_New_Id__c = NULL
```

**Compare tax IDs to identify overlap.**

### To Assess Matching Key Quality

**ES Org Analysis:**
```sql
SELECT
  COUNT(Id) as Total_Accounts,
  COUNT(Tax_ID__c) as With_Tax_ID,
  COUNT(CASE WHEN Tax_ID__c != NULL THEN 1 END) * 100.0 / COUNT(Id) as Percent_Populated
FROM Account
WHERE BBF_New_Id__c = NULL
```

---

## APPENDIX B: CONTACT INFORMATION

**For questions or clarifications:**

- **Migration Technical Lead:** [Name/Email]
- **BBF Salesforce Administrator:** [Name/Email]
- **ES Business Analyst:** [Name/Email]
- **Project Manager:** [Name/Email]

**Document Version:** 1.0
**Last Updated:** 2026-01-14
**Next Review Date:** [To be scheduled after decision]

# ES Contact to BBF Contact Field Mapping Summary

**Generated**: 2026-01-15
**Approach**: AI-Powered Semantic Matching (v2)
**Output File**: `ES_Contact_to_BBF_Contact_mapping.xlsx`

## Statistics

| Metric | Count |
|--------|-------|
| **Total BBF Contact Fields** | 88 |
| **Excluded Fields** | 23 (14 system + 9 Day 1) |
| **BBF Fields to Map** | 66 |
| **Total ES Contact Fields** | 239 |
| **High Confidence Matches** | 43 |
| **Medium Confidence Matches** | 0 |
| **Low Confidence Matches** | 1 |
| **No Match (BBF-Specific)** | 22 |
| **Transformers Needed** | 1 (Contact_Type__c) |
| **Picklist Fields Mapped** | 2 (Contact_Type__c, LeadSource) |
| **Total Picklist Values** | 47 |
| **Exact Picklist Matches** | 31 |
| **Close Picklist Matches** | 12 |
| **No Picklist Match** | 4 |

## AI Semantic Matching Highlights

- 43 exact matches for standard Salesforce Contact fields
- CRM domain intelligence identified semantic translations (Decision Maker → Executive, On-Site → Hands & Feet)
- Only 1 transformer required vs. 5 in fuzzy matching approach
- BBF has 17 contact types vs. 9 in ES (more granular operational needs)
- 22 BBF fields are genuinely new functionality (Marketing Cloud, contact status, formula validations)

## Key Picklist Mappings

### Contact_Type__c (NEEDS TRANSFORMER)
- ES: 9 values → BBF: 17 values
- Exact matches: Billing, Maintenance
- Semantic: Decision Maker → Executive, On-Site → Hands & Feet, Order → Service Order, Portal User → Main, Repair → Technician, Unknown → Prospect
- No match: Payable (needs business decision)

### LeadSource
- ES: 11 values → BBF: 21 values (includes "Legacy ES")
- Exact: Agent, ZoomInfo
- Close: Directly Engaged → Direct Contact, Tidio Chatbot → Website, Sales Intern → Employee Referral
- No match: CoStar, Network Map Leads, Neustar (ES-specific)

### Salutation & GeocodeAccuracy
- EXACT MATCH - No transformation needed
- All values identical between ES and BBF

## Files Generated

1. ES_Contact_to_BBF_Contact_mapping.xlsx (2 sheets: Field_Mapping, Picklist_Mapping)
2. day-two/exports/contact_mapping.json (source data)
3. day-two/tools/contact_semantic_matcher.py (matching script)

## Next Steps

1. Business review Contact_Type__c translations
2. Decide which ES lead score field to migrate (Lead_Score__c vs Campaign_Score__c vs Total_Lead_Score__c)
3. Build Contact_Type__c transformer
4. Test with POC data (192 contacts)

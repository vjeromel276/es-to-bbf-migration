#!/usr/bin/env python3
"""Query ES OrderItem Product distribution for mapping to BBF Product_Simple__c"""

from simple_salesforce import Salesforce

# Connect to ES UAT
sf = Salesforce(
    username='sfdcapi@everstream.net.uat',
    password='ZXasqw1234!@#$',
    security_token='X0ation2CNmK5C0pV94M6vFYS',
    domain='test'
)

print("Connected to ES UAT")
print()

from collections import Counter

# Query OrderItems for BBF-eligible Orders
query = '''
SELECT Id, Product_Name__c, Product_Family__c, Description
FROM OrderItem
WHERE Order.Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
AND (Order.Project_Group__c = null OR (NOT Order.Project_Group__c LIKE '%PA MARKET DECOM%'))
LIMIT 5000
'''

print("Querying ES OrderItem Product distribution (up to 5000 records)...")
result = sf.query_all(query)
records = result['records']
print(f"Retrieved {len(records)} OrderItem records")

# Aggregate by Product_Name__c
product_counter = Counter()
family_counter = Counter()
combo_counter = Counter()

for r in records:
    name = r.get('Product_Name__c') or '(null)'
    family = r.get('Product_Family__c') or '(null)'
    product_counter[name] += 1
    family_counter[family] += 1
    combo_counter[(name, family)] += 1

print()
print("=" * 90)
print("PRODUCT_NAME__c Distribution (Top 30)")
print("=" * 90)
print(f"{'Product_Name__c':60} | Count | %")
print("-" * 90)
for name, cnt in product_counter.most_common(30):
    pct = cnt / len(records) * 100
    print(f"{name:60} | {cnt:5} | {pct:.1f}%")

print()
print("=" * 90)
print("PRODUCT_FAMILY__c Distribution")
print("=" * 90)
print(f"{'Product_Family__c':40} | Count | %")
print("-" * 90)
for family, cnt in family_counter.most_common():
    pct = cnt / len(records) * 100
    print(f"{family:40} | {cnt:5} | {pct:.1f}%")

print()
print("-" * 90)
print(f"Total unique Product_Name__c: {len(product_counter)}")
print(f"Total unique Product_Family__c: {len(family_counter)}")
print(f"Total OrderItems analyzed: {len(records)}")

# Now check BBF Product_Simple__c picklist values
print()
print("=" * 90)
print("BBF Product_Simple__c Picklist Values")
print("=" * 90)

bbf_sf = Salesforce(
    username='vlettau@everstream.net',
    password='MNlkpo0987)(*&',
    security_token='I4xmQLmm03cXl1O9qI2Z3XAAX',
    domain='test'
)

# Get Service_Charge__c describe
desc = bbf_sf.Service_Charge__c.describe()
for field in desc['fields']:
    if field['name'] == 'Product_Simple__c':
        print(f"Field: {field['name']} ({field['label']})")
        print(f"Type: {field['type']}")
        print(f"Required: {not field['nillable']}")
        print(f"\nPicklist Values:")
        for pv in field['picklistValues']:
            active = "ACTIVE" if pv['active'] else "INACTIVE"
            default = " (default)" if pv.get('defaultValue') else ""
            print(f"  - {pv['value']}{default} [{active}]")
        print(f"\nTotal values: {len(field['picklistValues'])}")
        break

# Also check Service_Type_Charge__c
print()
print("=" * 90)
print("BBF Service_Type_Charge__c Picklist Values")
print("=" * 90)

for field in desc['fields']:
    if field['name'] == 'Service_Type_Charge__c':
        print(f"Field: {field['name']} ({field['label']})")
        print(f"Type: {field['type']}")
        print(f"Required: {not field['nillable']}")
        print(f"\nPicklist Values:")
        for pv in field['picklistValues']:
            active = "ACTIVE" if pv['active'] else "INACTIVE"
            default = " (default)" if pv.get('defaultValue') else ""
            print(f"  - {pv['value']}{default} [{active}]")
        print(f"\nTotal values: {len(field['picklistValues'])}")
        break

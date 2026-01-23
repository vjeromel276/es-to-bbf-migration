#!/usr/bin/env python3
"""Analyze ES OrderItem Description patterns for bandwidth extraction."""

from collections import Counter
from simple_salesforce import Salesforce
import re

# Connect to ES UAT
sf = Salesforce(
    username='sfdcapi@everstream.net.uat',
    password='ZXasqw1234!@#$',
    security_token='X0ation2CNmK5C0pV94M6vFYS',
    domain='test'
)

# Query - also get Product_Name__c
query = '''
SELECT Description, Product_Family__c, Product_Name__c
FROM OrderItem
WHERE Order.Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress')
AND (Order.Project_Group__c = null OR (NOT Order.Project_Group__c LIKE '%PA MARKET DECOM%'))
LIMIT 5000
'''

result = sf.query_all(query)
records = result['records']

# Analyze descriptions
desc_counter = Counter()
pattern_counter = Counter()

# Patterns to look for
patterns = {
    'Mbps pattern': r'\d+\s*Mbps',
    'Gbps pattern': r'\d+\s*Gbps',
    'MB pattern': r'\d+\s*MB',
    'GB pattern': r'\d+\s*GB',
    'Leading zero Mbps': r'0\d+Mbps',
    'Leading zero Gbps': r'0\d+Gbps',
    'Internet': r'Internet',
    'Ethernet': r'Ethernet',
    'Transport': r'Transport',
    'Dark Fiber': r'Dark Fiber',
    'Voice': r'Voice',
    'IP': r'IP',
}

product_name_counter = Counter()
product_pattern_counter = Counter()

for r in records:
    desc = r.get('Description') or ''
    product_name = r.get('Product_Name__c') or ''

    desc_counter[desc[:60]] += 1  # Truncate for counting
    product_name_counter[product_name[:60]] += 1

    for name, pattern in patterns.items():
        if re.search(pattern, desc, re.IGNORECASE):
            pattern_counter[name] += 1
        if re.search(pattern, product_name, re.IGNORECASE):
            product_pattern_counter[name] += 1

print("Top 30 Description values:")
print("=" * 80)
for desc, count in desc_counter.most_common(30):
    print(f"{count:5} | {desc}")

print()
print("Pattern matches in Descriptions:")
print("=" * 80)
for name, count in pattern_counter.most_common():
    pct = count / len(records) * 100
    print(f"{name:25} | {count:5} ({pct:.1f}%)")

print()
print("=" * 80)
print("Top 30 Product_Name__c values:")
print("=" * 80)
for name, count in product_name_counter.most_common(30):
    print(f"{count:5} | {name}")

print()
print("Pattern matches in Product_Name__c:")
print("=" * 80)
for name, count in product_pattern_counter.most_common():
    pct = count / len(records) * 100
    print(f"{name:25} | {count:5} ({pct:.1f}%)")

print()
print(f"Total records: {len(records)}")

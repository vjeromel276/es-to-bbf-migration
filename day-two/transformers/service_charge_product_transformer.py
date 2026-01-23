#!/usr/bin/env python3
"""
Service Charge Product Transformer

Transforms ES OrderItem Product data to BBF Service_Charge__c fields:
- Product_Family__c → Service_Type_Charge__c
- Description (bandwidth extraction) → Product_Simple__c

Usage:
    from transformers.service_charge_product_transformer import (
        transform_service_type_charge,
        transform_product_simple,
        extract_bandwidth_from_description
    )

    # Transform a single record
    service_type = transform_service_type_charge(es_orderitem['Product_Family__c'])
    product_simple = transform_product_simple(es_orderitem['Description'], es_orderitem['Product_Family__c'])
"""

import re
from typing import Optional, Tuple

# =============================================================================
# PRODUCT_FAMILY → SERVICE_TYPE_CHARGE MAPPING
# =============================================================================
# This mapping was generated from data analysis and AI suggestions.
# Update based on business review of the mapping template.

FAMILY_TO_SERVICE_TYPE = {
    # High Confidence Mappings
    'Point-to-Point (PTPS)': 'EPL',
    'Dark Fiber (DFBR)': 'DF',
    'Dark Fiber Pair IRU (DFBR)': 'DF',
    'Dedicated Internet Access (DIAS)': 'DIA',
    'Internet Only (DIAS)': 'DIA',
    'Virtual Dedicated Internet Access (VDIA)': 'DIA',
    'Hosted Voice (VOIC)': 'VOICE',
    'PRI (SIP) (VOIC)': 'VOICE',
    'SS7  (VOIC)': 'SS7',
    'Collocation (COLO)': 'COLO',
    'Rack (COLO)': 'COLO',
    'Power (COLO)': 'Power',
    'Network-to-Network Interface (NNIS)': 'ENNI',
    'Ethernet (EPL/EVPL) (ETHS)': 'EPL',
    'Ethernet Transport Only (ETHS)': 'EPL',
    'Dedicated DWDM (DWDM)': 'Wavelength',
    'Managed Wave (MWAV)': 'Wavelength',
    'TSP Fee': 'TSP',
    'Equipment & Managed Equipment': 'Equipment',

    # Medium Confidence Mappings
    'Point-to-MultiPoint (PMPS)': 'ELAN',
    'Private Line (PVLS)': 'EPL',
    'Data Center Services (CLDS)': 'COLO',
    'IP': 'IP Subnet',
    'Promotions': 'Credit',
    'NRC (Non-Recurring Charge)': 'Installation',
    'Tagged / Untagged': 'VLAN',
    'Routing': 'L3VPN',
    'Additional Port': 'XCN',
    'Managed Service (MSP)': 'Equipment',  # Default - update based on business

    # Low Confidence - Default Values (UPDATE BASED ON BUSINESS REVIEW)
    'Work Order - Unknown (WOUK)': 'Installation',  # 28.7% of records - NEEDS REVIEW
    'Work Order - Labor (WOLB)': 'Installation',
    'Handoff Type': 'XCN',
    'Logical Attributes': 'EPL',
    'Diversity': 'EPL',
    'Tandem': 'SS7',
}

# Default value when no mapping found
DEFAULT_SERVICE_TYPE = 'EPL'


# =============================================================================
# BANDWIDTH EXTRACTION PATTERNS
# =============================================================================
# Patterns to extract bandwidth from Description field
# Order matters - more specific patterns first

BANDWIDTH_PATTERNS = [
    # Patterns with explicit units
    (r'(\d+)\s*Gbps', 'Gbps'),
    (r'(\d+)\s*Mbps', 'Mbps'),
    (r'(\d+)Gbps', 'Gbps'),
    (r'(\d+)Mbps', 'Mbps'),

    # Patterns with leading zeros (e.g., "0100Mbps", "01Gbps")
    (r'0*(\d+)Gbps', 'Gbps'),
    (r'0*(\d+)Mbps', 'Mbps'),

    # Patterns in description text
    (r'(\d+)\s*GB', 'Gbps'),
    (r'(\d+)\s*MB', 'Mbps'),
    (r'(\d+)G\b', 'Gbps'),
    (r'(\d+)M\b', 'Mbps'),
]

# Mapping of extracted bandwidth to BBF Product_Simple__c values
# These are the exact picklist values in BBF
BANDWIDTH_TO_PRODUCT = {
    # Gbps values
    '1 Gbps': '1 Gbps',
    '2 Gbps': '2 Gbps',
    '3 Gbps': '3 Gbps',
    '4 Gbps': '4 Gbps',
    '5 Gbps': '5 Gbps',
    '6 Gbps': '6 Gbps',
    '7 Gbps': '7 Gbps',
    '8 Gbps': '8 Gbps',
    '9 Gbps': '9 Gbps',
    '10 Gbps': '10 Gbps',
    '20 Gbps': '20 Gbps',
    '25 Gbps': '25 Gbps',
    '30 Gbps': '30 Gbps',
    '40 Gbps': '40 Gbps',
    '50 Gbps': '50 Gbps',
    '60 Gbps': '60 Gbps',
    '70 Gbps': '70 Gbps',
    '80 Gbps': '80 Gbps',
    '90 Gbps': '90 Gbps',
    '100 Gbps': '100 Gbps',
    '200 Gbps': '200 Gbps',
    '300 Gbps': '300 Gbps',
    '400 Gbps': '400 Gbps',
    '800 Gbps': '800 Gbps',

    # Mbps values
    '5 Mbps': '5 Mbps',
    '10 Mbps': '10 Mbps',
    '20 Mbps': '20 Mbps',
    '50 Mbps': '50 Mbps',
    '100 Mbps': '100 Mbps',
    '200 Mbps': '200 Mbps',
    '250 Mbps': '250 Mbps',
    '300 Mbps': '300 Mbps',
    '400 Mbps': '400 Mbps',
    '500 Mbps': '500 Mbps',
    '600 Mbps': '600 Mbps',
    '700 Mbps': '700 Mbps',
    '750 Mbps': '750 Mbps',
    '800 Mbps': '800 Mbps',
    '900 Mbps': '900 Mbps',
}

# =============================================================================
# PRODUCT_NAME → PRODUCT_SIMPLE DIRECT MAPPING
# =============================================================================
# Maps ES Product_Name__c directly to BBF Product_Simple__c
# This provides better coverage than bandwidth extraction alone

PRODUCT_NAME_TO_PRODUCT_SIMPLE = {
    # Internet/DIA products
    'Dedicated Internet Access': 'DIA',
    'Internet': 'DIA',
    'Virtual Dedicated Internet Access': 'DIA',

    # Dark Fiber products
    'Dark Fiber': 'Dark Fiber',
    'Dark Fiber IRU': 'Dark Fiber',
    'Dark Fiber Lease': 'Dark Fiber',
    '2 Strands': 'Dark Fiber',
    '4 Strands': 'Dark Fiber',
    '6 Strands': 'Dark Fiber',
    '8 Strands': 'Dark Fiber',
    '12 Strands': 'Dark Fiber',
    '24 Strands': 'Dark Fiber',
    '48 Strands': 'Dark Fiber',
    '60 Strands': 'Dark Fiber',
    '72 Strands': 'Dark Fiber',
    '96 Strands': 'Dark Fiber',
    '144 Strands': 'Dark Fiber',

    # Ethernet products
    'Ethernet': 'Ethernet Transport',
    'Ethernet (EPL/EVPL)': 'Ethernet Transport',
    'Point-to-Point': 'Ethernet Transport',
    'Point-to-MultiPoint': 'Ethernet Transport',
    'Private Line': 'Ethernet Transport',

    # IP products
    'IPv4 Blocks /30  (1 Gateway, 1 Usable)': '/30 Static IP',
    'IPv4 Blocks /29  (1 Gateway, 5 Usable)': '/29 Static IP',
    'IPv4 Blocks /28  (1 Gateway, 13 Usable)': '/28 Static IP',
    'IPv4 Blocks /27  (1 Gateway, 29 Usable)': '/27 Static IP',
    'IPv4 Blocks /26  (1 Gateway, 61 Usable)': '/26 Static IP',
    'IPv4 Blocks /25  (1 Gateway, 125 Usable)': '/25 Static IP',
    'IPv4 Blocks /24  (1 Gateway, 253 Usable)': '/24 Static IP',
    'eBGP': 'IP ADDR',

    # Voice products
    'Voice Recurring Charges': 'Voice Trunk',
    'Hosted Voice': 'Voice Trunk',
    'PRI': 'Voice Trunk',
    'SIP': 'Voice Trunk',
    'Toll Free': 'Toll Free',
    'DID': 'DID',

    # Colocation products
    'Collocation': 'COLO',
    'Colocation': 'COLO',
    'Full Cabinet': 'Full Cabinet',
    'Half Cabinet': 'Half Cabinet',
    'Cabinet Relocate': 'COLO',
    'Rack Space': 'Rack Unit',
    'Floor Space': 'Floor Space',
    'Power': 'AC Power',

    # Cross-connect products
    'Cross Connect': 'Cross Connect',
    'Handoff Type : Copper': 'Cross Connect',
    'Handoff Type : Fiber': 'Cross Connect',

    # DWDM/Wavelength products
    'DWDM': 'Wavelength',
    'Managed Wave': 'Wavelength',
    'Wavelength': 'Wavelength',

    # Network products
    'Network-to-Network Interface': 'ENNI',
    'NNI': 'ENNI',

    # Logical/VLAN products
    'Logical Attribute : Layer 2': 'VLAN',
    'Logical Attribute : Layer 3': 'L3VPN',
    'Tagged': 'VLAN',
    'Untagged': 'VLAN',

    # Labor/Installation products
    'Labor': 'Install',
    'Installation': 'Install',
    'Expedite': 'Expedite',
    'Smart Hands': 'Smart Hands Hourly',

    # Promotions/Credits/Discounts
    'Discount': 'DISCOUNT',
    'Credit': 'Credit',
    'New Service Promotion: First 3 Months Free': 'Credit',
    'New Service Promotion: First 5 Months Free': 'Credit',
    'New Service Promotion:  First 5 Months Free': 'Credit',

    # Equipment
    'Rocket Fiber Service Delivery Device': 'EqpLease',
    'Equipment': 'EqpLease',
    'Router': 'EqpLease',

    # Diversity products
    'Diversity': 'Ethernet Transport',
    'Diverse Path': 'Ethernet Transport',

    # TSP products
    'TSP': 'TSP-MRC',
    'TSP Fee': 'TSP-MRC',

    # SS7 products
    'SS7': 'SS7',
    'ISUP': 'SS7',

    # Catch-all for unknown/undetermined
    'Unknown': 'ANNUAL',  # Default - business may want to review
    '00000_UNDETERMINED': 'ANNUAL',  # Default
}

# Service Type → Default Product mapping (when no bandwidth or product name match)
SERVICE_TYPE_DEFAULT_PRODUCTS = {
    'DIA': 'DIA',
    'DF': 'Dark Fiber',
    'EPL': 'Ethernet Transport',
    'EVPL': 'Ethernet Transport',
    'ELAN': 'Ethernet Transport',
    'COLO': 'COLO',
    'VOICE': 'Voice Trunk',
    'SS7': 'SS7',
    'Power': 'AC Power',
    'ENNI': 'ENNI',
    'Wavelength': 'Wavelength',
    'L3VPN': 'L3VPN',
    'VLAN': 'VLAN',
    'Installation': 'Install',
    'Credit': 'Credit',
    'Equipment': 'EqpLease',
    'IP Subnet': 'IP ADDR',
    'TSP': 'TSP-MRC',
    'XCN': 'XCONN',
}

# Ultimate default
DEFAULT_PRODUCT_SIMPLE = 'ANNUAL'


# =============================================================================
# TRANSFORMER FUNCTIONS
# =============================================================================

def extract_bandwidth_from_description(description: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract bandwidth value and unit from description field.

    Args:
        description: ES OrderItem Description field

    Returns:
        Tuple of (value, unit) e.g., (100, 'Mbps') or (None, None) if not found
    """
    if not description:
        return None, None

    for pattern, unit in BANDWIDTH_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                value = int(match.group(1))
                # Filter out unrealistic values
                if unit == 'Gbps' and value > 1000:
                    continue
                if unit == 'Mbps' and value > 10000:
                    continue
                return value, unit
            except (ValueError, IndexError):
                continue

    return None, None


def transform_service_type_charge(product_family: Optional[str]) -> str:
    """
    Transform ES Product_Family__c to BBF Service_Type_Charge__c.

    Args:
        product_family: ES OrderItem.Product_Family__c value

    Returns:
        BBF Service_Type_Charge__c picklist value
    """
    if not product_family:
        return DEFAULT_SERVICE_TYPE

    # Direct mapping lookup
    if product_family in FAMILY_TO_SERVICE_TYPE:
        return FAMILY_TO_SERVICE_TYPE[product_family]

    # Try partial matching for variations
    product_family_upper = product_family.upper()

    if 'DARK FIBER' in product_family_upper or 'DFBR' in product_family_upper:
        return 'DF'
    if 'INTERNET' in product_family_upper or 'DIA' in product_family_upper:
        return 'DIA'
    if 'VOICE' in product_family_upper or 'VOIC' in product_family_upper:
        return 'VOICE'
    if 'COLO' in product_family_upper:
        return 'COLO'
    if 'ETHERNET' in product_family_upper or 'EPL' in product_family_upper or 'EVPL' in product_family_upper:
        return 'EPL'
    if 'POINT-TO-POINT' in product_family_upper or 'PTPS' in product_family_upper:
        return 'EPL'
    if 'POINT-TO-MULTI' in product_family_upper or 'PMPS' in product_family_upper:
        return 'ELAN'
    if 'WAVE' in product_family_upper or 'DWDM' in product_family_upper:
        return 'Wavelength'

    return DEFAULT_SERVICE_TYPE


def transform_product_simple(
    description: Optional[str],
    product_family: Optional[str] = None,
    service_type: Optional[str] = None,
    product_name: Optional[str] = None
) -> str:
    """
    Transform ES OrderItem data to BBF Product_Simple__c.

    Priority:
    1. Direct Product_Name__c mapping (most specific)
    2. Extract bandwidth from Description field
    3. Extract bandwidth from Product_Name__c field
    4. Use service-type-based default
    5. Use ultimate default

    Args:
        description: ES OrderItem.Description field
        product_family: ES OrderItem.Product_Family__c (for context)
        service_type: Already-transformed Service_Type_Charge__c (for default lookup)
        product_name: ES OrderItem.Product_Name__c (may contain bandwidth or direct mapping)

    Returns:
        BBF Product_Simple__c picklist value
    """
    # Priority 1: Direct Product_Name__c mapping
    if product_name and product_name in PRODUCT_NAME_TO_PRODUCT_SIMPLE:
        return PRODUCT_NAME_TO_PRODUCT_SIMPLE[product_name]

    # Priority 2: Try to extract bandwidth from description
    bw_value, bw_unit = extract_bandwidth_from_description(description)

    # Priority 3: If not found in description, try Product_Name__c for bandwidth
    if bw_value is None and product_name:
        bw_value, bw_unit = extract_bandwidth_from_description(product_name)

    if bw_value is not None:
        # Construct bandwidth string
        bw_str = f"{bw_value} {bw_unit}"

        # Check if exact match exists
        if bw_str in BANDWIDTH_TO_PRODUCT:
            return BANDWIDTH_TO_PRODUCT[bw_str]

        # Try to find closest match
        if bw_unit == 'Gbps':
            # Find closest Gbps value
            gbps_values = [int(k.split()[0]) for k in BANDWIDTH_TO_PRODUCT.keys() if 'Gbps' in k]
            if gbps_values:
                closest = min(gbps_values, key=lambda x: abs(x - bw_value))
                return f"{closest} Gbps"
        elif bw_unit == 'Mbps':
            # Find closest Mbps value
            mbps_values = [int(k.split()[0]) for k in BANDWIDTH_TO_PRODUCT.keys() if 'Mbps' in k]
            if mbps_values:
                closest = min(mbps_values, key=lambda x: abs(x - bw_value))
                return f"{closest} Mbps"

    # No bandwidth found - use service type default
    if service_type and service_type in SERVICE_TYPE_DEFAULT_PRODUCTS:
        return SERVICE_TYPE_DEFAULT_PRODUCTS[service_type]

    # Try to derive from product family
    if product_family:
        derived_service_type = transform_service_type_charge(product_family)
        if derived_service_type in SERVICE_TYPE_DEFAULT_PRODUCTS:
            return SERVICE_TYPE_DEFAULT_PRODUCTS[derived_service_type]

    return DEFAULT_PRODUCT_SIMPLE


def transform_service_charge_products(es_orderitem: dict) -> dict:
    """
    Transform ES OrderItem to BBF Service_Charge__c product fields.

    Args:
        es_orderitem: ES OrderItem record dict

    Returns:
        Dict with transformed product fields:
        {
            'Service_Type_Charge__c': '...',
            'Product_Simple__c': '...'
        }
    """
    product_family = es_orderitem.get('Product_Family__c')
    description = es_orderitem.get('Description')
    product_name = es_orderitem.get('Product_Name__c')

    # Transform Service_Type_Charge__c first
    service_type = transform_service_type_charge(product_family)

    # Transform Product_Simple__c using service type context
    product_simple = transform_product_simple(description, product_family, service_type, product_name)

    return {
        'Service_Type_Charge__c': service_type,
        'Product_Simple__c': product_simple
    }


# =============================================================================
# TESTING / EXAMPLES
# =============================================================================

if __name__ == '__main__':
    # Test examples
    test_cases = [
        {'Product_Family__c': 'Point-to-Point (PTPS)', 'Description': '0100Mbps Ethernet Transport'},
        {'Product_Family__c': 'Dedicated Internet Access (DIAS)', 'Description': '01Gbps Internet'},
        {'Product_Family__c': 'Dark Fiber (DFBR)', 'Description': '2 Strands Dark Fiber'},
        {'Product_Family__c': 'Work Order - Unknown (WOUK)', 'Description': 'Unknown'},
        {'Product_Family__c': 'Hosted Voice (VOIC)', 'Description': 'Voice Recurring Charges'},
        {'Product_Family__c': 'Collocation (COLO)', 'Description': 'Full Cabinet'},
        {'Product_Family__c': None, 'Description': '50Mbps Ethernet'},
    ]

    print("Service Charge Product Transformer - Test Cases")
    print("=" * 80)

    for case in test_cases:
        result = transform_service_charge_products(case)
        bw = extract_bandwidth_from_description(case.get('Description'))

        print(f"\nInput:")
        print(f"  Product_Family__c: {case.get('Product_Family__c')}")
        print(f"  Description: {case.get('Description')}")
        print(f"  Extracted Bandwidth: {bw}")
        print(f"Output:")
        print(f"  Service_Type_Charge__c: {result['Service_Type_Charge__c']}")
        print(f"  Product_Simple__c: {result['Product_Simple__c']}")

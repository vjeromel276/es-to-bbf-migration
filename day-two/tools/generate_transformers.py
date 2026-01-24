#!/usr/bin/env python3
"""
Generate Python transformation functions from mapping Excel files.

This script reads mapping Excel files and generates Python modules with
transformer functions for fields marked with Transformer_Needed=Y.

Usage:
    # Generate transformers for a specific mapping
    python generate_transformers.py --mapping path/to/mapping.xlsx --output path/to/output.py

    # Generate transformers for all mappings
    python generate_transformers.py --all

    # Dry run - show what would be generated without writing files
    python generate_transformers.py --mapping path/to/mapping.xlsx --dry-run
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
    from openpyxl import load_workbook
except ImportError:
    print("Error: Required packages not installed. Run: pip install pandas openpyxl")
    sys.exit(1)


# Mapping directory
MAPPINGS_DIR = Path(__file__).parent.parent / "mappings"
TRANSFORMERS_DIR = Path(__file__).parent.parent / "transformers"


def safe_str(value) -> str:
    """Safely convert value to string, handling NaN/None/float."""
    if value is None:
        return ''
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return ''
        return str(value)
    return str(value)


def extract_object_name(filename: str) -> Tuple[str, str]:
    """Extract ES and BBF object names from mapping filename."""
    # Pattern: ES_{ESObject}_to_BBF_{BBFObject}_mapping.xlsx
    match = re.match(r'ES_(.+?)_to_BBF_(.+?)_mapping\.xlsx', filename)
    if match:
        return match.group(1), match.group(2)
    return 'Unknown', 'Unknown'


def get_default_value(bbf_type: str, is_required: bool) -> str:
    """Get the appropriate default value for a field type."""
    type_lower = safe_str(bbf_type).lower()

    if 'string' in type_lower or 'text' in type_lower or 'textarea' in type_lower:
        return "''" if is_required else "None"
    elif 'number' in type_lower or 'currency' in type_lower or 'double' in type_lower or 'percent' in type_lower:
        return "0.0" if is_required else "None"
    elif 'boolean' in type_lower or 'checkbox' in type_lower:
        return "False"
    elif 'date' in type_lower:
        return "None"
    elif 'picklist' in type_lower or 'multipicklist' in type_lower:
        return "None"  # Will be handled by lookup
    elif 'reference' in type_lower or 'lookup' in type_lower:
        return "None"
    else:
        return "None"


def get_type_hint(sf_type: str) -> str:
    """Get Python type hint for a Salesforce field type."""
    type_lower = safe_str(sf_type).lower()

    if 'string' in type_lower or 'text' in type_lower or 'textarea' in type_lower or 'picklist' in type_lower:
        return "str"
    elif 'number' in type_lower or 'currency' in type_lower or 'double' in type_lower or 'percent' in type_lower:
        return "float"
    elif 'boolean' in type_lower or 'checkbox' in type_lower:
        return "bool"
    elif 'datetime' in type_lower:
        return "datetime"
    elif 'date' in type_lower:
        return "date"
    elif 'int' in type_lower:
        return "int"
    else:
        return "Any"


def generate_transformation_logic(es_type: str, bbf_type: str, es_field: str, bbf_field: str, notes: str) -> str:
    """Generate the transformation logic based on type conversion needs."""
    es_lower = safe_str(es_type).lower()
    bbf_lower = safe_str(bbf_type).lower()

    # DateTime to Date
    if 'datetime' in es_lower and 'date' in bbf_lower and 'datetime' not in bbf_lower:
        return """    # Convert datetime to date
    if isinstance(es_value, datetime):
        return es_value.date()
    elif isinstance(es_value, date):
        return es_value
    elif isinstance(es_value, str):
        try:
            parsed = datetime.fromisoformat(es_value.replace('Z', '+00:00'))
            return parsed.date()
        except (ValueError, AttributeError):
            return None
    return None"""

    # String to Number
    if ('string' in es_lower or 'text' in es_lower) and ('number' in bbf_lower or 'double' in bbf_lower or 'currency' in bbf_lower):
        return """    # Convert string to number
    if isinstance(es_value, (int, float)):
        return float(es_value)
    elif isinstance(es_value, str):
        # Remove currency symbols, commas, whitespace
        cleaned = re.sub(r'[\\$,\\s]', '', es_value)
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    return 0.0"""

    # Number to String
    if ('number' in es_lower or 'double' in es_lower or 'currency' in es_lower) and ('string' in bbf_lower or 'text' in bbf_lower):
        return """    # Convert number to string
    if es_value is None:
        return ''
    return str(es_value)"""

    # Picklist to Picklist (value mapping)
    if 'picklist' in es_lower and 'picklist' in bbf_lower:
        field_upper = bbf_field.upper().replace('__C', '').replace('__c', '')
        return f"""    # Map picklist values using lookup dictionary
    if es_value is None:
        return None
    es_str = str(es_value).strip()
    return {field_upper}_MAP.get(es_str, es_str)  # Return original if no mapping"""

    # Multipicklist to Multipicklist
    if 'multipicklist' in es_lower and 'multipicklist' in bbf_lower:
        field_upper = bbf_field.upper().replace('__C', '').replace('__c', '')
        return f"""    # Map multipicklist values using lookup dictionary
    if es_value is None:
        return None
    es_str = str(es_value).strip()
    if not es_str:
        return None
    # Split by semicolon, map each value, rejoin
    values = [v.strip() for v in es_str.split(';')]
    mapped = [{field_upper}_MAP.get(v, v) for v in values if v]
    return ';'.join(mapped) if mapped else None"""

    # Boolean conversion
    if 'boolean' in bbf_lower or 'checkbox' in bbf_lower:
        return """    # Convert to boolean
    if es_value is None:
        return False
    if isinstance(es_value, bool):
        return es_value
    if isinstance(es_value, str):
        return es_value.lower() in ('true', 'yes', '1', 'y')
    return bool(es_value)"""

    # Default - pass through with type coercion
    return """    # Pass through with basic type handling
    return es_value"""


def generate_transformer_function(
    bbf_field: str,
    bbf_label: str,
    bbf_type: str,
    bbf_required: str,
    es_field: str,
    es_label: str,
    es_type: str,
    notes: str
) -> str:
    """Generate a single transformer function."""
    is_required = safe_str(bbf_required).lower() == 'yes'
    default_value = get_default_value(bbf_type, is_required)
    return_type = get_type_hint(bbf_type)

    # Clean field names for function name
    func_name = bbf_field.lower().replace('__c', '').replace('__', '_')
    func_name = re.sub(r'[^a-z0-9_]', '_', func_name)

    transformation_logic = generate_transformation_logic(es_type, bbf_type, es_field, bbf_field, notes)

    docstring = f'''    """
    Transform ES {es_field} to BBF {bbf_field}.

    ES Field: {es_field} ({es_label})
    ES Type: {es_type}

    BBF Field: {bbf_field} ({bbf_label})
    BBF Type: {bbf_type}
    BBF Required: {bbf_required}

    AI Reasoning:
    {notes if notes else 'Type conversion required between ES and BBF field types.'}

    Args:
        es_value: The source value from ES {es_field}
        context: Optional dict with additional record context

    Returns:
        Transformed value suitable for BBF {bbf_field}
    """'''

    function_code = f'''
def transform_{func_name}(es_value: Any, context: dict = None) -> Optional[{return_type}]:
{docstring}
    # Handle null/empty input
    if es_value is None or (isinstance(es_value, str) and not es_value.strip()):
        return {default_value}

{transformation_logic}
'''

    return function_code


def generate_picklist_maps(picklist_df: pd.DataFrame) -> str:
    """Generate picklist mapping dictionaries from picklist mapping sheet."""
    if picklist_df is None or picklist_df.empty:
        return ""

    # Group by BBF field
    maps_code = []

    for bbf_field in picklist_df['BBF_Field'].dropna().unique():
        field_rows = picklist_df[picklist_df['BBF_Field'] == bbf_field]

        # Create mapping dict
        field_upper = bbf_field.upper().replace('__C', '').replace('__c', '')
        mapping_items = []

        for _, row in field_rows.iterrows():
            es_value = row.get('ES_Picklist_Value', '')
            # Use BBF_Final_Value if populated, otherwise Suggested_Mapping if it's not a list
            bbf_value = row.get('BBF_Final_Value', '')
            if not bbf_value or pd.isna(bbf_value):
                suggested = row.get('Suggested_Mapping', '')
                notes = row.get('Notes', '')
                # Only use suggested if it's an exact or close match (not a list)
                if notes in ('Exact Match', 'Close Match') and suggested and not pd.isna(suggested):
                    bbf_value = suggested
                else:
                    bbf_value = es_value  # Keep original if no mapping

            if es_value and not pd.isna(es_value):
                # Escape quotes in values
                es_escaped = str(es_value).replace("'", "\\'")
                bbf_escaped = str(bbf_value).replace("'", "\\'") if bbf_value and not pd.isna(bbf_value) else es_escaped
                mapping_items.append(f"    '{es_escaped}': '{bbf_escaped}'")

        if mapping_items:
            map_code = f"{field_upper}_MAP = {{\n" + ",\n".join(mapping_items) + "\n}\n"
            maps_code.append(map_code)

    return "\n".join(maps_code)


def generate_transformer_module(
    excel_path: Path,
    es_object: str,
    bbf_object: str,
    field_df: pd.DataFrame,
    picklist_df: pd.DataFrame
) -> str:
    """Generate the complete transformer module."""

    # Filter to fields needing transformation
    needs_transform = field_df[field_df['Transformer_Needed'] == 'Y']

    if needs_transform.empty:
        return f'''#!/usr/bin/env python3
"""
Auto-generated transformation functions for ES {es_object} to BBF {bbf_object} migration.

Generated by: transformation-generator agent
Date: {datetime.now().isoformat()}
Source: {excel_path.name}

No transformers needed - all field mappings are direct.
"""

# No transformers required for this object
TRANSFORMERS = {{}}

def apply_transformers(es_record: dict) -> dict:
    """No transformations needed - return empty dict."""
    return {{}}
'''

    # Generate imports
    imports = '''#!/usr/bin/env python3
"""
Auto-generated transformation functions for ES {es_object} to BBF {bbf_object} migration.

Generated by: transformation-generator agent
Date: {timestamp}
Source: {excel_filename}

Usage:
    from transformers.{module_name}_transformers import TRANSFORMERS, apply_transformers

    # Apply single transformer
    bbf_value = TRANSFORMERS['{example_field}'](es_record['{example_es_field}'])

    # Apply all transformers
    bbf_record = apply_transformers(es_record)
"""

import re
from typing import Any, Optional
from datetime import datetime, date

'''.format(
        es_object=es_object,
        bbf_object=bbf_object,
        timestamp=datetime.now().isoformat(),
        excel_filename=excel_path.name,
        module_name=bbf_object.lower().replace('__c', ''),
        example_field=needs_transform.iloc[0]['BBF_Field_API_Name'] if not needs_transform.empty else 'field',
        example_es_field=needs_transform.iloc[0]['ES_Field_API_Name'] if not needs_transform.empty else 'field'
    )

    # Generate picklist maps
    picklist_maps = generate_picklist_maps(picklist_df)

    # Generate transformer functions
    transformer_functions = []
    transformer_registry = []
    field_mapping = []

    for _, row in needs_transform.iterrows():
        bbf_field = row['BBF_Field_API_Name']
        es_field = row['ES_Field_API_Name']

        if not bbf_field or pd.isna(bbf_field):
            continue

        func_name = bbf_field.lower().replace('__c', '').replace('__', '_')
        func_name = re.sub(r'[^a-z0-9_]', '_', func_name)

        func_code = generate_transformer_function(
            bbf_field=bbf_field,
            bbf_label=row.get('BBF_Field_Label', ''),
            bbf_type=row.get('BBF_Data_Type', ''),
            bbf_required=row.get('BBF_Is_Required', 'No'),
            es_field=es_field if es_field and not pd.isna(es_field) else '',
            es_label=row.get('ES_Field_Label', ''),
            es_type=row.get('ES_Data_Type', ''),
            notes=row.get('Notes', '')
        )
        transformer_functions.append(func_code)
        transformer_registry.append(f"    '{bbf_field}': transform_{func_name}")

        if es_field and not pd.isna(es_field):
            field_mapping.append(f"    '{bbf_field}': '{es_field}'")

    # Generate TRANSFORMERS registry
    transformers_dict = "TRANSFORMERS = {\n" + ",\n".join(transformer_registry) + "\n}\n"

    # Generate FIELD_MAPPING
    field_mapping_dict = "FIELD_MAPPING = {\n" + ",\n".join(field_mapping) + "\n}\n"

    # Generate apply_transformers function
    apply_func = '''

def apply_transformers(es_record: dict) -> dict:
    """
    Apply all transformers to an ES record.

    Args:
        es_record: Dictionary of ES field values (field API name -> value)

    Returns:
        Dictionary of transformed BBF field values (BBF field API name -> value)
    """
    bbf_record = {}

    for bbf_field, transformer in TRANSFORMERS.items():
        es_field = FIELD_MAPPING.get(bbf_field)
        if es_field and es_field in es_record:
            try:
                bbf_record[bbf_field] = transformer(es_record[es_field], es_record)
            except Exception as e:
                # Log error but continue with other fields
                print(f"Warning: Transform failed for {bbf_field}: {e}")
                bbf_record[bbf_field] = None

    return bbf_record
'''

    # Combine all parts
    module_code = imports
    if picklist_maps:
        module_code += "\n# Picklist value mappings\n" + picklist_maps + "\n"
    module_code += "\n".join(transformer_functions)
    module_code += "\n\n# Transformer registry\n" + transformers_dict
    module_code += "\n# Field mapping (BBF -> ES)\n" + field_mapping_dict
    module_code += apply_func

    return module_code


def process_mapping_file(excel_path: Path, output_path: Optional[Path] = None, dry_run: bool = False) -> dict:
    """Process a single mapping Excel file and generate transformer module."""
    print(f"\nProcessing: {excel_path.name}")

    # Extract object names
    es_object, bbf_object = extract_object_name(excel_path.name)
    print(f"  ES Object: {es_object}")
    print(f"  BBF Object: {bbf_object}")

    # Read Excel sheets
    try:
        field_df = pd.read_excel(excel_path, sheet_name='Field_Mapping')
        print(f"  Field mappings: {len(field_df)}")
    except Exception as e:
        print(f"  Error reading Field_Mapping sheet: {e}")
        return {'error': str(e)}

    try:
        picklist_df = pd.read_excel(excel_path, sheet_name='Picklist_Mapping')
        print(f"  Picklist mappings: {len(picklist_df)}")
    except Exception:
        print("  No Picklist_Mapping sheet found")
        picklist_df = None

    # Count transformers needed
    needs_transform = field_df[field_df['Transformer_Needed'] == 'Y']
    print(f"  Transformers needed: {len(needs_transform)}")

    if len(needs_transform) == 0:
        print("  No transformers needed for this mapping")
        return {
            'excel_path': str(excel_path),
            'es_object': es_object,
            'bbf_object': bbf_object,
            'transformers_needed': 0,
            'transformers_generated': 0
        }

    # Generate module code
    module_code = generate_transformer_module(
        excel_path=excel_path,
        es_object=es_object,
        bbf_object=bbf_object,
        field_df=field_df,
        picklist_df=picklist_df
    )

    # Determine output path
    if output_path is None:
        module_name = bbf_object.lower().replace('__c', '')
        output_path = TRANSFORMERS_DIR / f"{module_name}_transformers.py"

    if dry_run:
        print(f"\n  [DRY RUN] Would write to: {output_path}")
        print(f"\n  Generated code preview (first 2000 chars):\n")
        print(module_code[:2000])
        if len(module_code) > 2000:
            print(f"\n  ... ({len(module_code) - 2000} more characters)")
    else:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write module
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(module_code)
        print(f"  Written to: {output_path}")

        # Verify syntax
        try:
            compile(module_code, str(output_path), 'exec')
            print("  Syntax verification: PASSED")
        except SyntaxError as e:
            print(f"  Syntax verification: FAILED - {e}")

    return {
        'excel_path': str(excel_path),
        'output_path': str(output_path),
        'es_object': es_object,
        'bbf_object': bbf_object,
        'transformers_needed': len(needs_transform),
        'transformers_generated': len(needs_transform),
        'picklist_mappings': len(picklist_df) if picklist_df is not None else 0
    }


def process_all_mappings(dry_run: bool = False) -> List[dict]:
    """Process all mapping Excel files in the mappings directory."""
    results = []

    # Find all mapping Excel files
    mapping_files = list(MAPPINGS_DIR.glob('ES_*_to_BBF_*_mapping.xlsx'))
    print(f"Found {len(mapping_files)} mapping files")

    for excel_path in sorted(mapping_files):
        result = process_mapping_file(excel_path, dry_run=dry_run)
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Generate Python transformation functions from mapping Excel files'
    )
    parser.add_argument(
        '--mapping',
        type=Path,
        help='Path to specific mapping Excel file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for transformer module (default: day-two/transformers/{object}_transformers.py)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all mapping files in day-two/mappings/'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be generated without writing files'
    )

    args = parser.parse_args()

    if args.all:
        print("=" * 60)
        print("GENERATING TRANSFORMERS FOR ALL MAPPING FILES")
        print("=" * 60)
        results = process_all_mappings(dry_run=args.dry_run)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        total_transformers = sum(r.get('transformers_generated', 0) for r in results)
        print(f"Files processed: {len(results)}")
        print(f"Total transformers generated: {total_transformers}")

        for r in results:
            if 'error' not in r:
                print(f"  {r['es_object']} -> {r['bbf_object']}: {r['transformers_generated']} transformers")

    elif args.mapping:
        if not args.mapping.exists():
            print(f"Error: Mapping file not found: {args.mapping}")
            sys.exit(1)

        result = process_mapping_file(args.mapping, args.output, dry_run=args.dry_run)

        if 'error' in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"\nGenerated {result['transformers_generated']} transformer functions")

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python generate_transformers.py --all")
        print("  python generate_transformers.py --mapping day-two/mappings/ES_Account_to_BBF_Account_mapping.xlsx")
        print("  python generate_transformers.py --all --dry-run")


if __name__ == '__main__':
    main()

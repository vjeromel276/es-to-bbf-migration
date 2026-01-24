#!/usr/bin/env python3
"""
ES Data Profiler - Analyze actual production data to inform field mapping decisions.

This tool queries actual ES Salesforce records and provides:
1. Field population rates (% null vs. populated)
2. Picklist value distributions (actual usage, not just metadata)
3. Sample data for validation
4. Data patterns and edge cases
5. String field length analysis

Usage:
    # Profile a single object with default sample size
    python es_data_profiler.py --object Account

    # Profile with custom sample size and output directory
    python es_data_profiler.py --object Order --sample-size 10000 --output-dir ../data-profiles

    # Profile multiple objects
    python es_data_profiler.py --object Account Order Contact --sample-size 5000

    # Filter by BBF migration criteria (for Order)
    python es_data_profiler.py --object Order --filter-bbf-orders

    # Generate comprehensive report with sample records
    python es_data_profiler.py --object Account --include-samples --sample-records 50
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import pandas as pd
    from simple_salesforce import Salesforce
except ImportError:
    print("Error: Required packages not installed. Run: pip install pandas simple-salesforce")
    sys.exit(1)

# ---------------------------------------------------------------------
# Salesforce credentials (ES Production)
# ---------------------------------------------------------------------
SF_USERNAME = "sfdcapi@everstream.net"
SF_PASSWORD = "pV4CAxns8DQtJsBq!"
SF_TOKEN = "r1uoYiusK19RbrflARydi86TA"
SF_DOMAIN = "login"  # or 'test' for sandbox

# ---------------------------------------------------------------------
# Migration filtering constants
# ---------------------------------------------------------------------
ACTIVE_STATUSES = ["Activated", "Suspended (Late Payment)", "Disconnect in Progress"]
WD_PROJECT_GROUP = "PA MARKET DECOM"

# Fields to exclude from analysis
SYSTEM_FIELDS = {
    'Id', 'IsDeleted', 'MasterRecordId', 'CreatedDate', 'CreatedById',
    'LastModifiedDate', 'LastModifiedById', 'SystemModstamp',
    'LastActivityDate', 'LastViewedDate', 'LastReferencedDate'
}

# Day 1 migration fields (already migrated)
DAY_1_FIELDS = {
    'Name', 'OwnerId', 'ES_Legacy_ID__c', 'BBF_New_Id__c'
}


class ESDataProfiler:
    """Profiles actual ES Salesforce data to inform migration decisions."""

    def __init__(self, sf: Salesforce, object_name: str, sample_size: int = 5000,
                 filter_bbf_orders: bool = False, include_samples: bool = False,
                 sample_records: int = 20):
        self.sf = sf
        self.object_name = object_name
        self.sample_size = sample_size
        self.filter_bbf_orders = filter_bbf_orders
        self.include_samples = include_samples
        self.sample_records = sample_records
        self.metadata = None
        self.records = []

    def get_metadata(self) -> Dict:
        """Fetch object metadata."""
        print(f"📡 Fetching metadata for {self.object_name}...")
        try:
            desc = self.sf.__getattr__(self.object_name).describe()
            self.metadata = desc
            print(f"✅ Retrieved metadata for {len(desc.get('fields', []))} fields")
            return desc
        except Exception as e:
            print(f"❌ Error fetching metadata: {e}")
            sys.exit(1)

    def build_soql_query(self, fields: List[str]) -> str:
        """Build SOQL query with optional filtering."""
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM {self.object_name}"

        # Add filtering for Order object if requested
        if self.filter_bbf_orders and self.object_name == 'Order':
            status_list = "', '".join(ACTIVE_STATUSES)
            query += f" WHERE Status IN ('{status_list}')"
            query += f" AND (Project_Group__c = NULL OR Project_Group__c NOT LIKE '%{WD_PROJECT_GROUP}%')"

        query += f" LIMIT {self.sample_size}"
        return query

    def query_records(self, fields: List[str]) -> List[Dict]:
        """Query actual records from Salesforce."""
        query = self.build_soql_query(fields)
        print(f"🔍 Querying {self.object_name} records...")
        print(f"   Query: {query[:150]}{'...' if len(query) > 150 else ''}")

        try:
            result = self.sf.query(query)
            self.records = result.get('records', [])
            print(f"✅ Retrieved {len(self.records)} records")
            return self.records
        except Exception as e:
            print(f"❌ Error querying records: {e}")
            print(f"   Full query: {query}")
            sys.exit(1)

    def analyze_field_population(self, field_name: str, field_type: str) -> Dict:
        """Analyze population rate and patterns for a field."""
        total = len(self.records)
        if total == 0:
            return {
                'total_records': 0,
                'populated': 0,
                'null': 0,
                'population_rate': 0.0,
                'null_rate': 0.0
            }

        populated = 0
        null_count = 0
        values = []

        for record in self.records:
            value = record.get(field_name)
            if value is None or value == '':
                null_count += 1
            else:
                populated += 1
                values.append(value)

        return {
            'total_records': total,
            'populated': populated,
            'null': null_count,
            'population_rate': round((populated / total) * 100, 2),
            'null_rate': round((null_count / total) * 100, 2),
            'values': values
        }

    def analyze_picklist_distribution(self, field_name: str,
                                     possible_values: List[str]) -> Dict:
        """Analyze actual picklist value usage vs. metadata."""
        stats = self.analyze_field_population(field_name, 'picklist')
        values = stats['values']

        if not values:
            return {
                'total_records': stats['total_records'],
                'populated': stats['populated'],
                'null_count': stats['null'],
                'population_rate': stats['population_rate'],
                'unique_values_used': 0,
                'total_possible_values': len(possible_values),
                'usage_rate': 0.0,
                'value_distribution': {},
                'unused_values': possible_values,
                'undefined_values': []
            }

        # Count actual usage
        value_counts = Counter(values)
        unique_used = set(values)
        possible_set = set(possible_values)

        # Calculate percentages
        value_distribution = {
            val: {
                'count': count,
                'percentage': round((count / len(values)) * 100, 2)
            }
            for val, count in value_counts.most_common()
        }

        # Find unused and undefined values
        unused = sorted(list(possible_set - unique_used))
        undefined = sorted(list(unique_used - possible_set))

        return {
            'total_records': stats['total_records'],
            'populated': stats['populated'],
            'null_count': stats['null'],
            'population_rate': stats['population_rate'],
            'unique_values_used': len(unique_used),
            'total_possible_values': len(possible_values),
            'usage_rate': round((len(unique_used) / len(possible_values)) * 100, 2) if possible_values else 0.0,
            'value_distribution': value_distribution,
            'unused_values': unused,
            'undefined_values': undefined
        }

    def analyze_multipicklist_distribution(self, field_name: str,
                                          possible_values: List[str]) -> Dict:
        """Analyze multipicklist field (semicolon-separated values)."""
        stats = self.analyze_field_population(field_name, 'multipicklist')
        values = stats['values']

        if not values:
            return {
                'total_records': stats['total_records'],
                'populated': stats['populated'],
                'null_count': stats['null'],
                'population_rate': stats['population_rate'],
                'unique_values_used': 0,
                'total_possible_values': len(possible_values),
                'value_distribution': {},
                'unused_values': possible_values,
                'undefined_values': [],
                'combination_patterns': {}
            }

        # Parse multipicklist values
        all_individual_values = []
        combination_counts = Counter()

        for val in values:
            val_str = str(val).strip()
            if val_str:
                combination_counts[val_str] += 1
                parts = [v.strip() for v in val_str.split(';') if v.strip()]
                all_individual_values.extend(parts)

        # Count individual value usage
        value_counts = Counter(all_individual_values)
        unique_used = set(all_individual_values)
        possible_set = set(possible_values)

        # Calculate percentages
        value_distribution = {
            val: {
                'count': count,
                'percentage': round((count / len(all_individual_values)) * 100, 2) if all_individual_values else 0
            }
            for val, count in value_counts.most_common()
        }

        # Top combinations
        combination_patterns = {
            combo: {
                'count': count,
                'percentage': round((count / len(values)) * 100, 2)
            }
            for combo, count in combination_counts.most_common(10)
        }

        # Find unused and undefined
        unused = sorted(list(possible_set - unique_used))
        undefined = sorted(list(unique_used - possible_set))

        return {
            'total_records': stats['total_records'],
            'populated': stats['populated'],
            'null_count': stats['null'],
            'population_rate': stats['population_rate'],
            'unique_values_used': len(unique_used),
            'total_possible_values': len(possible_values),
            'value_distribution': value_distribution,
            'unused_values': unused,
            'undefined_values': undefined,
            'combination_patterns': combination_patterns
        }

    def analyze_string_field(self, field_name: str, max_length: int) -> Dict:
        """Analyze string field lengths and patterns."""
        stats = self.analyze_field_population(field_name, 'string')
        values = stats['values']

        if not values:
            return {
                'total_records': stats['total_records'],
                'populated': stats['populated'],
                'population_rate': stats['population_rate'],
                'max_length_defined': max_length,
                'actual_max_length': 0,
                'actual_min_length': 0,
                'avg_length': 0,
                'exceeds_limit': 0,
                'truncation_needed': False
            }

        lengths = [len(str(v)) for v in values]
        max_actual = max(lengths) if lengths else 0
        min_actual = min(lengths) if lengths else 0
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        exceeds = sum(1 for length in lengths if length > max_length)

        return {
            'total_records': stats['total_records'],
            'populated': stats['populated'],
            'population_rate': stats['population_rate'],
            'max_length_defined': max_length,
            'actual_max_length': max_actual,
            'actual_min_length': min_actual,
            'avg_length': round(avg_length, 2),
            'exceeds_limit': exceeds,
            'truncation_needed': exceeds > 0
        }

    def analyze_numeric_field(self, field_name: str) -> Dict:
        """Analyze numeric field ranges and patterns."""
        stats = self.analyze_field_population(field_name, 'number')
        values = stats['values']

        if not values:
            return {
                'total_records': stats['total_records'],
                'populated': stats['populated'],
                'population_rate': stats['population_rate'],
                'min_value': None,
                'max_value': None,
                'avg_value': None
            }

        # Convert to numeric
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue

        if not numeric_values:
            return {
                'total_records': stats['total_records'],
                'populated': stats['populated'],
                'population_rate': stats['population_rate'],
                'min_value': None,
                'max_value': None,
                'avg_value': None
            }

        return {
            'total_records': stats['total_records'],
            'populated': stats['populated'],
            'population_rate': stats['population_rate'],
            'min_value': min(numeric_values),
            'max_value': max(numeric_values),
            'avg_value': round(sum(numeric_values) / len(numeric_values), 2)
        }

    def generate_field_profile(self, field: Dict) -> Dict:
        """Generate complete profile for a field."""
        field_name = field['name']
        field_type = field['type']
        field_label = field['label']

        # Skip system fields
        if field_name in SYSTEM_FIELDS:
            return None

        profile = {
            'field_name': field_name,
            'field_label': field_label,
            'field_type': field_type,
            'is_custom': field_name.endswith('__c'),
            'is_required': not field.get('nillable', True),
        }

        # Type-specific analysis
        if field_type == 'picklist':
            possible_values = [pv['value'] for pv in field.get('picklistValues', [])
                             if pv.get('active', True)]
            analysis = self.analyze_picklist_distribution(field_name, possible_values)
            profile.update(analysis)
            profile['analysis_type'] = 'picklist'

        elif field_type == 'multipicklist':
            possible_values = [pv['value'] for pv in field.get('picklistValues', [])
                             if pv.get('active', True)]
            analysis = self.analyze_multipicklist_distribution(field_name, possible_values)
            profile.update(analysis)
            profile['analysis_type'] = 'multipicklist'

        elif field_type in ['string', 'textarea', 'url', 'email', 'phone']:
            max_length = field.get('length', 255)
            analysis = self.analyze_string_field(field_name, max_length)
            profile.update(analysis)
            profile['analysis_type'] = 'string'

        elif field_type in ['double', 'currency', 'percent', 'int']:
            analysis = self.analyze_numeric_field(field_name)
            profile.update(analysis)
            profile['analysis_type'] = 'numeric'

        else:
            # Basic population analysis
            stats = self.analyze_field_population(field_name, field_type)
            profile.update(stats)
            profile['analysis_type'] = 'basic'

        return profile

    def get_sample_records(self, field_names: List[str]) -> List[Dict]:
        """Get sample records for manual review."""
        if not self.records:
            return []

        sample_size = min(self.sample_records, len(self.records))
        samples = self.records[:sample_size]

        # Extract only requested fields
        cleaned_samples = []
        for record in samples:
            cleaned = {field: record.get(field) for field in field_names}
            cleaned_samples.append(cleaned)

        return cleaned_samples

    def profile(self) -> Dict:
        """Run complete profiling analysis."""
        print(f"\n{'='*80}")
        print(f"PROFILING: {self.object_name}")
        print(f"{'='*80}\n")

        # Get metadata
        metadata = self.get_metadata()
        fields = metadata.get('fields', [])

        # Build field list for query
        queryable_fields = [f['name'] for f in fields
                           if f.get('type') not in ['base64', 'location', 'address']
                           and not f.get('compoundFieldName')]

        # Query records
        self.query_records(queryable_fields)

        # Profile each field
        print(f"\n📊 Analyzing {len(fields)} fields...")
        field_profiles = []

        for i, field in enumerate(fields, 1):
            field_name = field['name']
            if i % 20 == 0:
                print(f"   Processed {i}/{len(fields)} fields...")

            profile = self.generate_field_profile(field)
            if profile:
                field_profiles.append(profile)

        print(f"✅ Completed profiling {len(field_profiles)} fields")

        # Get sample records if requested
        sample_records = []
        if self.include_samples:
            print(f"\n📝 Extracting {self.sample_records} sample records...")
            sample_records = self.get_sample_records(queryable_fields[:30])  # Limit to first 30 fields
            print(f"✅ Extracted {len(sample_records)} sample records")

        return {
            'object_name': self.object_name,
            'profiled_at': datetime.now().isoformat(),
            'total_records_analyzed': len(self.records),
            'sample_size': self.sample_size,
            'filter_applied': self.filter_bbf_orders,
            'total_fields': len(field_profiles),
            'field_profiles': field_profiles,
            'sample_records': sample_records
        }


def export_to_csv(profile_data: Dict, output_dir: Path):
    """Export profiling data to CSV files."""
    object_name = profile_data['object_name']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export 1: Field Population Summary
    summary_file = output_dir / f"{object_name}_field_population_summary_{timestamp}.csv"
    print(f"\n💾 Exporting field population summary to {summary_file.name}...")

    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Field Name', 'Field Label', 'Field Type', 'Is Custom', 'Is Required',
            'Total Records', 'Populated', 'Null Count', 'Population Rate %',
            'Null Rate %', 'Analysis Type'
        ])

        for field in profile_data['field_profiles']:
            writer.writerow([
                field['field_name'],
                field['field_label'],
                field['field_type'],
                field['is_custom'],
                field['is_required'],
                field.get('total_records', 0),
                field.get('populated', 0),
                field.get('null_count', field.get('null', 0)),
                field.get('population_rate', 0),
                field.get('null_rate', 0),
                field.get('analysis_type', 'unknown')
            ])

    print(f"✅ Exported {len(profile_data['field_profiles'])} field summaries")

    # Export 2: Picklist Value Distributions
    picklist_file = output_dir / f"{object_name}_picklist_distributions_{timestamp}.csv"
    print(f"💾 Exporting picklist distributions to {picklist_file.name}...")

    picklist_count = 0
    with open(picklist_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Field Name', 'Field Label', 'Field Type', 'Picklist Value',
            'Count', 'Percentage', 'Status'
        ])

        for field in profile_data['field_profiles']:
            if field.get('analysis_type') in ['picklist', 'multipicklist']:
                picklist_count += 1
                field_name = field['field_name']
                field_label = field['field_label']
                field_type = field['field_type']

                # Write actual usage
                for value, stats in field.get('value_distribution', {}).items():
                    writer.writerow([
                        field_name, field_label, field_type, value,
                        stats['count'], stats['percentage'], 'USED'
                    ])

                # Write unused values
                for value in field.get('unused_values', []):
                    writer.writerow([
                        field_name, field_label, field_type, value,
                        0, 0.0, 'UNUSED'
                    ])

                # Write undefined values (not in metadata but found in data)
                for value in field.get('undefined_values', []):
                    writer.writerow([
                        field_name, field_label, field_type, value,
                        '?', '?', 'UNDEFINED (Not in metadata)'
                    ])

    print(f"✅ Exported distributions for {picklist_count} picklist fields")

    # Export 3: High-value field recommendations
    recommendations_file = output_dir / f"{object_name}_field_recommendations_{timestamp}.csv"
    print(f"💾 Exporting field recommendations to {recommendations_file.name}...")

    with open(recommendations_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Field Name', 'Field Label', 'Field Type', 'Population Rate %',
            'Recommendation', 'Reasoning'
        ])

        for field in profile_data['field_profiles']:
            field_name = field['field_name']
            field_label = field['field_label']
            field_type = field['field_type']
            pop_rate = field.get('population_rate', 0)

            recommendation = ''
            reasoning = ''

            # High population rate = good candidate for mapping
            if pop_rate >= 80:
                recommendation = 'PRIORITIZE'
                reasoning = f'{pop_rate}% populated - highly valuable field'
            elif pop_rate >= 50:
                recommendation = 'CONSIDER'
                reasoning = f'{pop_rate}% populated - moderate value'
            elif pop_rate >= 10:
                recommendation = 'LOW PRIORITY'
                reasoning = f'{pop_rate}% populated - sparse data'
            else:
                recommendation = 'SKIP'
                reasoning = f'{pop_rate}% populated - mostly null'

            # Additional insights
            if field.get('truncation_needed'):
                reasoning += f" | ⚠️ Truncation needed (max: {field.get('actual_max_length')} > limit: {field.get('max_length_defined')})"

            if field.get('undefined_values'):
                reasoning += f" | ⚠️ {len(field['undefined_values'])} undefined values in data"

            writer.writerow([
                field_name, field_label, field_type, pop_rate,
                recommendation, reasoning
            ])

    print(f"✅ Exported field recommendations")

    # Export 4: Sample records (if requested)
    if profile_data.get('sample_records'):
        samples_file = output_dir / f"{object_name}_sample_records_{timestamp}.csv"
        print(f"💾 Exporting sample records to {samples_file.name}...")

        df = pd.DataFrame(profile_data['sample_records'])
        df.to_csv(samples_file, index=False, encoding='utf-8')
        print(f"✅ Exported {len(profile_data['sample_records'])} sample records")

    print(f"\n✅ All exports completed to: {output_dir}/")
    return [summary_file, picklist_file, recommendations_file]


def main():
    parser = argparse.ArgumentParser(
        description="Profile ES Salesforce data to inform field mapping decisions"
    )
    parser.add_argument(
        '--object', '-o',
        nargs='+',
        required=True,
        help='Object API name(s) to profile (e.g., Account Order Contact)'
    )
    parser.add_argument(
        '--sample-size', '-s',
        type=int,
        default=5000,
        help='Number of records to sample (default: 5000)'
    )
    parser.add_argument(
        '--output-dir', '-d',
        default='../data-profiles',
        help='Output directory for profile reports (default: ../data-profiles)'
    )
    parser.add_argument(
        '--filter-bbf-orders',
        action='store_true',
        help='Apply BBF migration filter to Order queries (Active + NOT PA MARKET DECOM)'
    )
    parser.add_argument(
        '--include-samples',
        action='store_true',
        help='Include sample records in output'
    )
    parser.add_argument(
        '--sample-records',
        type=int,
        default=20,
        help='Number of sample records to export (default: 20)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Connect to Salesforce
    print("🔌 Connecting to ES Salesforce...")
    try:
        sf = Salesforce(
            username=SF_USERNAME,
            password=SF_PASSWORD,
            security_token=SF_TOKEN,
            domain=SF_DOMAIN
        )
        print(f"✅ Connected to: {sf.sf_instance}")
    except Exception as e:
        print(f"❌ Error connecting to Salesforce: {e}")
        sys.exit(1)

    # Process each object
    for obj_name in args.object:
        profiler = ESDataProfiler(
            sf=sf,
            object_name=obj_name,
            sample_size=args.sample_size,
            filter_bbf_orders=args.filter_bbf_orders,
            include_samples=args.include_samples,
            sample_records=args.sample_records
        )

        try:
            profile_data = profiler.profile()
            export_to_csv(profile_data, output_dir)

        except Exception as e:
            print(f"❌ Error profiling {obj_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*80}")
    print("✅ PROFILING COMPLETE")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

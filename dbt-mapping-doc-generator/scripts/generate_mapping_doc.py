#!/usr/bin/env python3
"""
dbt Model Mapping Documentation Generator

Reverse engineers comprehensive mapping documentation for dbt models by:
1. Parsing dbt SQL code to extract column lineage
2. Querying Snowflake for column metadata
3. Extracting descriptions from schema.yml files
4. Generating detailed mapping documentation in Google Sheets format

Author: Harikrishnan R
Version: 1.0.0
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

try:
    import snowflake.connector
except ImportError:
    print("Warning: snowflake-connector-python not installed")
    print("Install with: pip3 install snowflake-connector-python")

try:
    import sqlparse
except ImportError:
    print("Warning: sqlparse not installed")
    print("Install with: pip3 install sqlparse")


class DbtModelAnalyzer:
    """Analyzes dbt models to extract column lineage and metadata"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.models = {}
        self.schema_docs = {}
        
    def find_model_file(self, model_name: str, layer: str = None) -> Optional[str]:
        """Find SQL file for a given model name"""
        # Parse model name: layer__domain__table
        parts = model_name.split('__')
        if len(parts) >= 3:
            layer = parts[0]
            domain = parts[1]
            table = '__'.join(parts[2:])
        
        # Search in models directory
        if layer:
            search_path = f"{self.repo_path}/models/{layer}"
        else:
            search_path = f"{self.repo_path}/models"
        
        for root, dirs, files in os.walk(search_path):
            for file in files:
                if file.endswith('.sql') and model_name in file:
                    return os.path.join(root, file)
        
        return None
    
    def load_schema_yml(self, layer: str = None) -> Dict:
        """Load schema.yml files for documentation"""
        schema_docs = {}
        
        search_path = f"{self.repo_path}/models/{layer}" if layer else f"{self.repo_path}/models"
        
        for root, dirs, files in os.walk(search_path):
            for file in files:
                if file.endswith('__schema.yml') or file == 'schema.yml':
                    yml_path = os.path.join(root, file)
                    try:
                        with open(yml_path, 'r') as f:
                            data = yaml.safe_load(f)
                            if data and 'models' in data:
                                for model in data['models']:
                                    model_name = model.get('name')
                                    if model_name:
                                        schema_docs[model_name] = {
                                            'description': model.get('description', ''),
                                            'columns': {
                                                col['name']: {
                                                    'description': col.get('description', ''),
                                                    'tests': col.get('tests', [])
                                                }
                                                for col in model.get('columns', [])
                                            }
                                        }
                    except Exception as e:
                        print(f"Warning: Could not parse {yml_path}: {e}")
        
        return schema_docs
    
    def parse_sql_file(self, sql_file_path: str) -> Dict:
        """Parse dbt SQL file to extract column lineage"""
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Extract CTEs and final SELECT
        ctes = self._extract_ctes(sql_content)
        final_select = self._extract_final_select(sql_content)
        
        # Parse column transformations
        columns = self._parse_select_columns(final_select)
        
        # Extract source tables (ref/source)
        source_tables = self._extract_source_tables(sql_content)
        
        return {
            'sql_content': sql_content,
            'ctes': ctes,
            'final_select': final_select,
            'columns': columns,
            'source_tables': source_tables
        }
    
    def _extract_ctes(self, sql: str) -> Dict[str, str]:
        """Extract all CTEs from SQL"""
        ctes = {}
        
        # Pattern to match CTE definitions
        cte_pattern = r'(\w+)\s+as\s*\((.*?)\)(?=,\s*\w+\s+as\s*\(|,?\s*select)'
        
        matches = re.finditer(cte_pattern, sql, re.IGNORECASE | re.DOTALL)
        for match in matches:
            cte_name = match.group(1).strip()
            cte_body = match.group(2).strip()
            ctes[cte_name] = cte_body
        
        return ctes
    
    def _extract_final_select(self, sql: str) -> str:
        """Extract the final SELECT statement"""
        # Find the last SELECT that's not part of a CTE
        sql_clean = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)  # Remove comments
        
        # Split by CTEs
        parts = re.split(r'\bwith\b', sql_clean, flags=re.IGNORECASE)
        
        if len(parts) > 1:
            # Get everything after the last CTE
            after_ctes = parts[-1]
            # Find the final SELECT
            select_match = re.search(r'(select\s+.*?)(?:$|\bfrom\b)', after_ctes, re.IGNORECASE | re.DOTALL)
            if select_match:
                return select_match.group(0)
        
        # Fallback: get last SELECT statement
        select_matches = re.findall(r'select\s+.*?(?:from|$)', sql_clean, re.IGNORECASE | re.DOTALL)
        if select_matches:
            return select_matches[-1]
        
        return ""
    
    def _parse_select_columns(self, select_statement: str) -> List[Dict]:
        """Parse SELECT columns to extract column names and transformations"""
        columns = []
        
        # Remove SELECT keyword
        select_content = re.sub(r'^\s*select\s+', '', select_statement, flags=re.IGNORECASE).strip()
        
        # Remove FROM clause
        select_content = re.split(r'\bfrom\b', select_content, flags=re.IGNORECASE)[0]
        
        # Split by commas (but not within parentheses)
        column_strings = self._split_by_comma(select_content)
        
        for col_str in column_strings:
            col_str = col_str.strip()
            if not col_str:
                continue
            
            # Parse column with possible alias
            # Pattern: expression [as] alias
            as_match = re.search(r'(.+?)\s+(?:as\s+)?(\w+)$', col_str, re.IGNORECASE)
            
            if as_match:
                transformation = as_match.group(1).strip()
                column_name = as_match.group(2).strip()
            else:
                # Simple column reference
                transformation = col_str
                column_name = col_str.split('.')[-1].strip()
            
            # Extract source column(s) from transformation
            source_columns = self._extract_source_columns(transformation)
            
            columns.append({
                'column_name': column_name.upper(),
                'transformation': transformation,
                'source_columns': source_columns
            })
        
        return columns
    
    def _split_by_comma(self, text: str) -> List[str]:
        """Split by comma but respect parentheses and CASE statements"""
        parts = []
        current = []
        paren_depth = 0
        case_depth = 0
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check for CASE keyword
            if text[i:i+4].upper() == 'CASE':
                case_depth += 1
                current.append(text[i:i+4])
                i += 4
                continue
            
            # Check for END keyword
            if text[i:i+3].upper() == 'END':
                case_depth = max(0, case_depth - 1)
                current.append(text[i:i+3])
                i += 3
                continue
            
            if char == '(':
                paren_depth += 1
                current.append(char)
            elif char == ')':
                paren_depth -= 1
                current.append(char)
            elif char == ',' and paren_depth == 0 and case_depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)
            
            i += 1
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _extract_source_columns(self, transformation: str) -> List[str]:
        """Extract source column names from transformation expression"""
        # Remove functions and operators to find column references
        # Pattern: table.column or just column
        column_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\b'
        
        matches = re.findall(column_pattern, transformation)
        
        columns = []
        for match in matches:
            col = match[1]
            # Filter out SQL keywords
            if col.upper() not in ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'AS', 'CASE', 'WHEN', 
                                     'THEN', 'ELSE', 'END', 'NULL', 'TRUE', 'FALSE', 'IN', 'NOT',
                                     'IS', 'LIKE', 'BETWEEN', 'EXISTS', 'ALL', 'ANY']:
                columns.append(col.upper())
        
        return list(set(columns))
    
    def _extract_source_tables(self, sql: str) -> List[Dict]:
        """Extract source tables from ref() and source() functions"""
        sources = []
        
        # Extract ref() calls
        ref_pattern = r"ref\(['\"]([^'\"]+)['\"]\)"
        ref_matches = re.findall(ref_pattern, sql)
        for ref in ref_matches:
            sources.append({
                'type': 'ref',
                'name': ref,
                'full_name': ref
            })
        
        # Extract source() calls
        source_pattern = r"source\(['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\)"
        source_matches = re.findall(source_pattern, sql)
        for src in source_matches:
            sources.append({
                'type': 'source',
                'schema': src[0],
                'name': src[1],
                'full_name': f"{src[0]}__{src[1]}"
            })
        
        return sources


class SnowflakeMetadataExtractor:
    """Extracts metadata from Snowflake information_schema"""
    
    def __init__(self, account: str, user: str, role: str, warehouse: str):
        self.account = account
        self.user = user
        self.role = role
        self.warehouse = warehouse
        self.conn = None
    
    def connect(self):
        """Connect to Snowflake using browser SSO"""
        print(f"Connecting to Snowflake: {self.account}")
        print("Browser window will open for authentication...")
        
        self.conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            authenticator='externalbrowser',
            role=self.role,
            warehouse=self.warehouse
        )
        
        print("✓ Connected to Snowflake")
    
    def get_table_metadata(self, database: str, schema: str, table: str) -> Dict:
        """Get complete table and column metadata from Snowflake"""
        cursor = self.conn.cursor()
        
        # Get table description
        table_query = f"""
        SELECT TABLE_COMMENT
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema.upper()}'
        AND TABLE_NAME = '{table.upper()}'
        """
        
        cursor.execute(table_query)
        table_result = cursor.fetchone()
        table_description = table_result[0] if table_result and table_result[0] else ""
        
        # Get column metadata
        column_query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COMMENT
        FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema.upper()}'
        AND TABLE_NAME = '{table.upper()}'
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(column_query)
        columns = []
        
        for row in cursor.fetchall():
            columns.append({
                'column_name': row[0],
                'data_type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
                'comment': row[4] if row[4] else ""
            })
        
        cursor.close()
        
        return {
            'table_name': table,
            'table_description': table_description,
            'columns': columns
        }
    
    def close(self):
        """Close Snowflake connection"""
        if self.conn:
            self.conn.close()


class MappingDocGenerator:
    """Generates mapping documentation in Google Sheets format"""
    
    def __init__(self, dbt_analyzer: DbtModelAnalyzer, sf_extractor: SnowflakeMetadataExtractor):
        self.dbt_analyzer = dbt_analyzer
        self.sf_extractor = sf_extractor
    
    def generate_mapping_doc(self, model_name: str, layer: str = None) -> List[Dict]:
        """Generate complete mapping documentation for a model"""
        
        print(f"\n{'='*80}")
        print(f"Generating Mapping Documentation: {model_name}")
        print(f"{'='*80}\n")
        
        # Parse model name to get database/schema/table
        parts = model_name.split('__')
        if len(parts) >= 3:
            layer = parts[0]
            schema = parts[1]
            table = '__'.join(parts[2:])
        else:
            print(f"Error: Invalid model name format. Expected: layer__schema__table")
            return []
        
        # 1. Find and parse dbt SQL file
        print(f"1. Analyzing dbt SQL code...")
        model_file = self.dbt_analyzer.find_model_file(model_name, layer)
        
        if not model_file:
            print(f"   Warning: Could not find SQL file for {model_name}")
            dbt_data = {'columns': [], 'source_tables': []}
        else:
            print(f"   Found: {model_file}")
            dbt_data = self.dbt_analyzer.parse_sql_file(model_file)
            print(f"   Extracted {len(dbt_data['columns'])} columns")
        
        # 2. Load schema.yml documentation
        print(f"\n2. Loading schema documentation...")
        schema_docs = self.dbt_analyzer.load_schema_yml(layer)
        model_docs = schema_docs.get(model_name, {'description': '', 'columns': {}})
        print(f"   Found documentation for {len(model_docs['columns'])} columns")
        
        # 3. Get Snowflake metadata
        print(f"\n3. Querying Snowflake metadata...")
        database = layer.upper()  # SILVER, GOLD, etc.
        sf_metadata = self.sf_extractor.get_table_metadata(database, schema, table)
        print(f"   Retrieved metadata for {len(sf_metadata['columns'])} columns")
        
        # 4. Combine all data into mapping documentation
        print(f"\n4. Generating mapping documentation...")
        mapping_rows = []
        
        # Create lookup dictionaries
        dbt_columns = {col['column_name']: col for col in dbt_data.get('columns', [])}
        sf_columns = {col['column_name']: col for col in sf_metadata['columns']}
        
        # Iterate through all columns (union of dbt and Snowflake)
        all_columns = set(dbt_columns.keys()) | set(sf_columns.keys())
        
        for column_name in sorted(all_columns):
            dbt_col = dbt_columns.get(column_name, {})
            sf_col = sf_columns.get(column_name, {})
            col_docs = model_docs['columns'].get(column_name.lower(), {})
            
            # Determine upstream source
            upstream_tables = []
            upstream_columns = []
            transformation = dbt_col.get('transformation', '')
            
            if dbt_col.get('source_columns'):
                upstream_columns = dbt_col['source_columns']
            
            if dbt_data.get('source_tables'):
                upstream_tables = [src['full_name'] for src in dbt_data['source_tables']]
            
            mapping_row = {
                'Table Name': model_name,
                'Column Name': column_name,
                'Logical Column Name': self._to_logical_name(column_name),
                'Column Description': col_docs.get('description', '') or sf_col.get('comment', ''),
                'Table Description': model_docs.get('description', '') or sf_metadata.get('table_description', ''),
                'R3/R3+': self._determine_r3_status(transformation),
                'Value': sf_col.get('data_type', ''),
                'Remarks': self._generate_remarks(dbt_col, sf_col),
                'Queries': '',  # To be filled manually
                'Query team': '',  # To be filled manually
                'Comment': transformation if transformation else '',
                'Source Team': self._determine_source_team(layer, schema),
                'Upstream Table Name': ', '.join(upstream_tables) if upstream_tables else '',
                'Upstream Column Name': ', '.join(upstream_columns) if upstream_columns else '',
                'Additional Comments': self._generate_additional_comments(col_docs)
            }
            
            mapping_rows.append(mapping_row)
        
        print(f"   ✓ Generated {len(mapping_rows)} mapping rows")
        
        return mapping_rows
    
    def _to_logical_name(self, column_name: str) -> str:
        """Convert technical column name to logical name"""
        # Convert SNAKE_CASE to Title Case
        words = column_name.lower().split('_')
        return ' '.join(word.capitalize() for word in words)
    
    def _determine_r3_status(self, transformation: str) -> str:
        """Determine if column is R3 (direct) or R3+ (transformed)"""
        if not transformation:
            return ''
        
        # Simple heuristic: if transformation is just a column reference, it's R3
        if re.match(r'^\w+\.\w+$', transformation.strip()) or re.match(r'^\w+$', transformation.strip()):
            return 'R3'
        else:
            return 'R3+'
    
    def _generate_remarks(self, dbt_col: Dict, sf_col: Dict) -> str:
        """Generate remarks based on column analysis"""
        remarks = []
        
        if dbt_col.get('transformation'):
            trans = dbt_col['transformation']
            if 'CASE' in trans.upper():
                remarks.append('Contains conditional logic')
            if 'CAST' in trans.upper() or '::' in trans:
                remarks.append('Type conversion applied')
            if any(func in trans.upper() for func in ['SUM', 'AVG', 'COUNT', 'MAX', 'MIN']):
                remarks.append('Aggregation function')
        
        if sf_col.get('nullable'):
            remarks.append('Nullable')
        
        return '; '.join(remarks)
    
    def _determine_source_team(self, layer: str, schema: str) -> str:
        """Determine source team based on layer and schema"""
        team_mapping = {
            'core': 'Core Banking Team',
            'payment': 'Payment Team',
            'lending': 'Lending Team',
            'cards': 'Cards Team',
            'crm': 'CRM Team',
            'risk': 'Risk Team',
            'finance': 'Finance Team',
            'reg': 'Regulatory Team'
        }
        
        return team_mapping.get(schema.lower(), 'Data Platform Team')
    
    def _generate_additional_comments(self, col_docs: Dict) -> str:
        """Generate additional comments from tests and other metadata"""
        comments = []
        
        if col_docs.get('tests'):
            test_names = []
            for test in col_docs['tests']:
                if isinstance(test, str):
                    test_names.append(test)
                elif isinstance(test, dict):
                    test_names.extend(test.keys())
            
            if test_names:
                comments.append(f"Tests: {', '.join(test_names)}")
        
        return '; '.join(comments)
    
    def export_to_csv(self, mapping_rows: List[Dict], output_file: str):
        """Export mapping documentation to CSV (importable to Google Sheets)"""
        import csv
        
        if not mapping_rows:
            print("No data to export")
            return
        
        # Get all column headers
        headers = [
            'Table Name', 'Column Name', 'Logical Column Name', 'Column Description',
            'Table Description', 'R3/R3+', 'Value', 'Remarks', 'Queries', 'Query team',
            'Comment', 'Source Team', 'Upstream Table Name', 'Upstream Column Name',
            'Additional Comments'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(mapping_rows)
        
        print(f"\n✓ Exported to: {output_file}")
        print(f"  Import this CSV to Google Sheets")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate dbt model mapping documentation')
    parser.add_argument('--model', required=True, help='Model name (e.g., silver__core__casa)')
    parser.add_argument('--repo', required=True, help='Path to dbt repository')
    parser.add_argument('--sf-account', required=True, help='Snowflake account')
    parser.add_argument('--sf-user', required=True, help='Snowflake user')
    parser.add_argument('--sf-role', default='TRANSFORMER', help='Snowflake role')
    parser.add_argument('--sf-warehouse', default='TRANSFORM_WH', help='Snowflake warehouse')
    parser.add_argument('--output', default='mapping_doc.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Initialize analyzers
    print("Initializing dbt analyzer...")
    dbt_analyzer = DbtModelAnalyzer(args.repo)
    
    print("Connecting to Snowflake...")
    sf_extractor = SnowflakeMetadataExtractor(
        account=args.sf_account,
        user=args.sf_user,
        role=args.sf_role,
        warehouse=args.sf_warehouse
    )
    sf_extractor.connect()
    
    # Generate mapping documentation
    generator = MappingDocGenerator(dbt_analyzer, sf_extractor)
    mapping_rows = generator.generate_mapping_doc(args.model)
    
    # Export to CSV
    generator.export_to_csv(mapping_rows, args.output)
    
    # Cleanup
    sf_extractor.close()
    
    print(f"\n{'='*80}")
    print("✓ Mapping documentation generation complete!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

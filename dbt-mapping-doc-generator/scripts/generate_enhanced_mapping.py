#!/usr/bin/env python3
"""
Enhanced Comprehensive Mapping Doc Generator
With improved CASE statement parsing
"""

import json
import csv
import re
import yaml
from pathlib import Path
from collections import defaultdict

def extract_upstream_tables(sql_content):
    """Extract all ref() calls from SQL"""
    pattern = r'{{\s*ref\(["\']([^"\']+)["\']\)\s*}}'
    refs = re.findall(pattern, sql_content)
    return list(set(refs))

def extract_ctes(sql_content):
    """Extract all CTE definitions"""
    ctes = {}
    pattern = r'(\w+)\s+as\s*\('
    matches = re.finditer(pattern, sql_content, re.IGNORECASE)
    
    for match in matches:
        cte_name = match.group(1)
        if cte_name.lower() not in ['with', 'select', 'from', 'where', 'and', 'or']:
            ctes[cte_name] = True
    
    return list(ctes.keys())

def parse_final_select_enhanced(sql_content):
    """Enhanced parser for final CTE with better CASE handling"""
    columns = {}
    
    # Find the "final as" CTE
    final_pattern = r'final\s+as\s*\((.*?)\)\s*select\s+\*\s+from\s+final'
    match = re.search(final_pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        return columns
    
    final_cte = match.group(1)
    
    # Find the SELECT clause by line-by-line parsing
    # This avoids matching nested SELECT/FROM in subqueries
    lines = final_cte.split('\n')
    select_start = -1
    from_line = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped.startswith('select'):
            select_start = i
        elif select_start >= 0 and stripped.startswith('from'):
            from_line = i
            break
    
    if select_start < 0 or from_line < 0:
        return columns
    
    select_lines = lines[select_start + 1:from_line]  # Skip the SELECT keyword line
    select_clause = '\n'.join(select_lines)
    
    # Parse column by column, handling CASE statements properly
    columns = parse_select_columns(select_clause)
    
    return columns

def parse_select_columns(select_clause):
    """Parse SELECT clause to extract column definitions with CASE support"""
    columns = {}
    
    # Remove comments
    select_clause = re.sub(r'--.*?\n', '\n', select_clause)
    
    # Remove Jinja templates ({% ... %}) - replace with placeholder
    select_clause = re.sub(r'{%.*?%}', ' [jinja_template] ', select_clause, flags=re.DOTALL)
    
    # Split by commas, but respect CASE...END blocks
    col_expressions = split_by_comma_respecting_case(select_clause)
    
    for expr in col_expressions:
        expr = expr.strip()
        if not expr:
            continue
        
        # Extract "expression as column_name"
        as_match = re.search(r'^(.*?)\s+as\s+(\w+)\s*$', expr, re.IGNORECASE | re.DOTALL)
        
        if as_match:
            expression = as_match.group(1).strip()
            col_name = as_match.group(2).strip().upper()
            
            # Clean up expression
            expression = ' '.join(expression.split())  # Normalize whitespace
            
            columns[col_name] = {
                'expression': expression,
                'source_column': extract_source_column(expression),
                'is_case': 'case' in expression.lower()
            }
    
    return columns

def split_by_comma_respecting_case(text):
    """Split by comma but respect CASE...END blocks"""
    expressions = []
    current = ""
    depth = 0
    paren_depth = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # Track CASE...END depth
        if i + 4 <= len(text) and text[i:i+4].lower() == 'case':
            # Make sure it's a word boundary
            if (i == 0 or not text[i-1].isalnum()) and (i+4 >= len(text) or not text[i+4].isalnum()):
                depth += 1
        
        if i + 3 <= len(text) and text[i:i+3].lower() == 'end':
            # Make sure it's a word boundary
            if (i == 0 or not text[i-1].isalnum()) and (i+3 >= len(text) or not text[i+3].isalnum()):
                depth = max(0, depth - 1)
        
        # Track parentheses
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth = max(0, paren_depth - 1)
        
        # Split on comma only if outside CASE and parentheses
        if char == ',' and depth == 0 and paren_depth == 0:
            expressions.append(current)
            current = ""
        else:
            current += char
        
        i += 1
    
    if current.strip():
        expressions.append(current)
    
    return expressions

def extract_source_column(expression):
    """Extract source column from expression"""
    # Handle simple cases like "txn.column_name"
    simple_match = re.search(r'(\w+)\.(\w+)', expression)
    if simple_match:
        return f"{simple_match.group(1)}.{simple_match.group(2)}"
    return ""

def extract_case_logic(expression):
    """Extract structured CASE logic"""
    if 'case' not in expression.lower():
        return None
    
    case_logic = {
        'conditions': [],
        'else_value': None
    }
    
    # Extract WHEN clauses (handle multiple formats)
    when_patterns = [
        r"when\s+(.*?)\s+then\s+'([^']*)'",  # when X then 'value'
        r'when\s+(.*?)\s+then\s+"([^"]*)"',  # when X then "value"
        r'when\s+(.*?)\s+then\s+(\d+)',      # when X then 123
        r"when\s+(.*?)\s+then\s+'([^']*)'",  # when X then 'value'
        r'when\s+(.*?)\s+then\s+(\w+)',      # when X then value
    ]
    
    for pattern in when_patterns:
        matches = re.finditer(pattern, expression, re.IGNORECASE | re.DOTALL)
        for match in matches:
            condition = match.group(1).strip()
            value = match.group(2).strip()
            
            # Clean up condition
            condition = ' '.join(condition.split())
            
            if condition and value:
                case_logic['conditions'].append({
                    'when': condition,
                    'then': value
                })
    
    # Extract ELSE clause
    else_patterns = [
        r"else\s+'([^']*)'",
        r'else\s+"([^"]*)"',
        r'else\s+(\d+)',
        r'else\s+(\w+)'
    ]
    
    for pattern in else_patterns:
        else_match = re.search(pattern, expression, re.IGNORECASE)
        if else_match:
            case_logic['else_value'] = else_match.group(1).strip()
            break
    
    return case_logic

def format_case_logic(case_logic):
    """Format CASE logic into readable text"""
    if not case_logic or not case_logic.get('conditions'):
        return ""
    
    lines = []
    for cond in case_logic['conditions']:
        when = cond['when']
        then = cond['then']
        # Shorten long conditions
        if len(when) > 50:
            when = when[:47] + "..."
        lines.append(f"WHEN {when} THEN '{then}'")
    
    if case_logic.get('else_value'):
        lines.append(f"ELSE '{case_logic['else_value']}'")
    
    return " | ".join(lines)

def load_schema_yml(repo_path, model_name):
    """Load schema.yml and extract tests/descriptions"""
    schema_info = {
        'columns': {},
        'model_description': ''
    }
    
    models_dir = Path(repo_path) / 'models'
    schema_files = list(models_dir.rglob('*schema.yml'))
    
    for schema_file in schema_files:
        try:
            with open(schema_file) as f:
                schema_data = yaml.safe_load(f)
                
            if not schema_data or 'models' not in schema_data:
                continue
            
            for model in schema_data['models']:
                if model.get('name') == model_name:
                    schema_info['model_description'] = model.get('description', '')
                    
                    for col in model.get('columns', []):
                        col_name = col['name'].upper()
                        tests = col.get('tests', [])
                        
                        dq_rules = []
                        enums = []
                        
                        for test in tests:
                            if isinstance(test, str):
                                dq_rules.append(test)
                            elif isinstance(test, dict):
                                for test_name, test_config in test.items():
                                    if 'accepted_values' in test_name:
                                        if 'values' in test_config:
                                            values = test_config['values']
                                            if isinstance(values, str):
                                                enums = re.findall(r"'([^']+)'", values)
                                            elif isinstance(values, list):
                                                enums = values
                                    else:
                                        dq_rules.append(f"{test_name}: {test_config}")
                        
                        schema_info['columns'][col_name] = {
                            'description': col.get('description', ''),
                            'dq_rules': dq_rules,
                            'enums': enums
                        }
                    
                    return schema_info
        except Exception as e:
            continue
    
    return schema_info

def generate_comprehensive_mapping(model_name, sql_file, sf_inventory_file, repo_path, output_file):
    """Generate comprehensive mapping documentation with enhanced CASE parsing"""
    
    print(f"\n{'='*80}")
    print(f"Generating Comprehensive Mapping Doc: {model_name}")
    print(f"{'='*80}\n")
    
    # 1. Load SQL file
    print("1. Parsing SQL file with enhanced CASE parser...")
    with open(sql_file) as f:
        sql_content = f.read()
    
    upstream_tables = extract_upstream_tables(sql_content)
    print(f"   ✓ Found {len(upstream_tables)} upstream tables")
    
    ctes = extract_ctes(sql_content)
    print(f"   ✓ Found {len(ctes)} CTEs")
    
    column_transformations = parse_final_select_enhanced(sql_content)
    print(f"   ✓ Parsed {len(column_transformations)} column transformations")
    
    case_count = sum(1 for c in column_transformations.values() if c.get('is_case'))
    print(f"   ✓ Identified {case_count} CASE statements")
    
    # 2. Load schema.yml
    print("\n2. Loading schema.yml...")
    schema_info = load_schema_yml(repo_path, model_name)
    print(f"   ✓ Found DQ rules for {len(schema_info['columns'])} columns")
    
    # 3. Load Snowflake metadata
    print("\n3. Loading Snowflake metadata...")
    with open(sf_inventory_file) as f:
        data = json.load(f)
    
    if model_name not in data['models']:
        print(f"   ERROR: Model not found in inventory")
        return
    
    model = data['models'][model_name]
    print(f"   ✓ Found {len(model['columns'])} columns")
    
    # 4. Generate mapping rows
    print("\n4. Generating mapping documentation...")
    mapping_rows = []
    
    for col in model['columns']:
        col_name = col['name']
        
        # Get transformation logic
        transformation = column_transformations.get(col_name, {})
        expression = transformation.get('expression', '')
        source_col = transformation.get('source_column', '')
        is_case = transformation.get('is_case', False)
        
        # Parse CASE logic if present
        case_logic = None
        case_summary = ""
        if is_case and expression:
            case_logic = extract_case_logic(expression)
            if case_logic:
                case_summary = format_case_logic(case_logic)
        
        # Get schema info
        schema_col = schema_info['columns'].get(col_name, {})
        dq_rules = schema_col.get('dq_rules', [])
        yaml_enums = schema_col.get('enums', [])
        
        # Extract enums from CASE logic
        case_enums = []
        if case_logic and case_logic.get('conditions'):
            case_enums = [c['then'] for c in case_logic['conditions']]
            if case_logic.get('else_value'):
                case_enums.append(case_logic['else_value'])
        
        # Determine upstream table
        upstream = ""
        upstream_col = ""
        if source_col:
            source_parts = source_col.split('.')
            source_table = source_parts[0] if len(source_parts) > 0 else ""
            upstream_col = source_parts[1] if len(source_parts) > 1 else ""
            
            # Map CTE alias back to upstream table
            cte_to_upstream = {
                'txn': 'bronze__core_transaction_history__transactions_posting',
                'raw_transactions': 'bronze__core_transaction_history__transactions_posting',
                'acct': 'bronze__projections__accounts__account_gl_id_mapping',
                'accounts': 'bronze__projections__accounts__account_gl_id_mapping',
                'casa_cust': 'silver__onboarding__customer_master',
                'casa_customers': 'silver__onboarding__customer_master',
                'biz_cust': 'biz_customer_ssic_mapping (macro)',
                'biz_customers': 'biz_customer_ssic_mapping (macro)'
            }
            upstream = cte_to_upstream.get(source_table, '')
        
        # Combine enums
        all_enums = case_enums + yaml_enums
        enum_str = ", ".join(all_enums[:10]) if all_enums else ""
        if len(all_enums) > 10:
            enum_str += f" ... ({len(all_enums)} total)"
        
        # Determine R3/R3+
        r3_type = "R3" if (not expression or expression == source_col or expression == 'null') else "R3+"
        
        # Use CASE summary if available, otherwise use expression
        transform_display = case_summary if case_summary else expression[:300]
        
        row = {
            'Table Name': f"{col['database']}.{col['schema']}.{model['table'].upper()}",
            'Column Name': col_name,
            'Logical Column Name': col_name.replace('_', ' ').title(),
            'Column Description': schema_col.get('description', ''),
            'Table Description': schema_info['model_description'],
            'R3/R3+': r3_type,
            'Transformation Logic': transform_display,
            'Remarks': '',
            'DQ Rules': '; '.join(dq_rules),
            'Enums/Accepted Values': enum_str,
            'Query team': '',
            'Comment': '',
            'Source Team': '',
            'Upstream Table Name': upstream,
            'Upstream Column Name': upstream_col,
            'Data Type': col['data_type'],
            'Nullable': str(col['nullable']),
            'Additional Comments': ''
        }
        mapping_rows.append(row)
    
    # 5. Add upstream tables summary
    print(f"\n5. Upstream Tables ({len(upstream_tables)}):")
    for table in sorted(upstream_tables):
        print(f"   - {table}")
    
    # 6. Write to CSV
    headers = [
        'Table Name',
        'Column Name',
        'Logical Column Name',
        'Column Description',
        'Table Description',
        'R3/R3+',
        'Transformation Logic',
        'Remarks',
        'DQ Rules',
        'Enums/Accepted Values',
        'Query team',
        'Comment',
        'Source Team',
        'Upstream Table Name',
        'Upstream Column Name',
        'Data Type',
        'Nullable',
        'Additional Comments'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(mapping_rows)
    
    print(f"\n{'='*80}")
    print(f"✓ Generated comprehensive mapping doc: {output_file}")
    print(f"  Total columns: {len(mapping_rows)}")
    print(f"  Upstream tables: {len(upstream_tables)}")
    print(f"  Columns with DQ rules: {sum(1 for r in mapping_rows if r['DQ Rules'])}")
    print(f"  Columns with enums: {sum(1 for r in mapping_rows if r['Enums/Accepted Values'])}")
    print(f"  Transformed columns (R3+): {sum(1 for r in mapping_rows if r['R3/R3+'] == 'R3+')}")
    print(f"  CASE statements parsed: {case_count}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 6:
        print("Usage: python3 generate_enhanced_mapping.py <model_name> <sql_file> <inventory_json> <repo_path> <output_csv>")
        print("\nExample:")
        print("  python3 generate_enhanced_mapping.py \\")
        print("    silver__core__casa_transactions \\")
        print("    /tmp/compare-gxs/models/silver/core/silver__core__casa_transactions.sql \\")
        print("    /tmp/gxs_inventory_snowflake.json \\")
        print("    /tmp/compare-gxs \\")
        print("    casa_transactions_enhanced.csv")
        sys.exit(1)
    
    model_name = sys.argv[1]
    sql_file = sys.argv[2]
    inventory_file = sys.argv[3]
    repo_path = sys.argv[4]
    output_file = sys.argv[5]
    
    generate_comprehensive_mapping(model_name, sql_file, inventory_file, repo_path, output_file)

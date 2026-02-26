#!/usr/bin/env python3
"""
Extract complete column information from Snowflake using browser-based SSO.
"""

import json
import sys
from collections import defaultdict

try:
    import snowflake.connector
except ImportError:
    print("ERROR: snowflake-connector-python not installed")
    print("Install with: pip3 install snowflake-connector-python")
    sys.exit(1)

def connect_to_snowflake(account, user, role, warehouse):
    """
    Connect to Snowflake using browser-based SSO authentication.
    This will open a browser window for authentication.
    """
    print(f"\nConnecting to Snowflake account: {account}")
    print(f"User: {user}")
    print(f"Role: {role}")
    print(f"Warehouse: {warehouse}")
    print("\n⚠️  A browser window will open for authentication...")
    print("Please complete the login in your browser.\n")
    
    try:
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            authenticator='externalbrowser',  # Browser-based SSO
            role=role,
            warehouse=warehouse
        )
        print("✓ Successfully connected to Snowflake!\n")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)

def get_all_columns_for_database(conn, database_name, schema_filter=None):
    """
    Query information_schema.columns for a specific database.
    Returns dict of {table_name: [column_info]}
    """
    print(f"Querying {database_name} database...")
    
    cursor = conn.cursor()
    
    # Query to get all columns
    query = f"""
    SELECT 
        table_schema,
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default,
        comment
    FROM {database_name}.information_schema.columns
    WHERE table_schema != 'INFORMATION_SCHEMA'
    ORDER BY table_schema, table_name, ordinal_position
    """
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Organize by table
        tables = defaultdict(list)
        for row in results:
            schema, table, col_name, position, dtype, nullable, default, comment = row
            
            # Create full table name with database prefix
            full_table_name = f"{database_name.lower()}__{schema.lower()}__{table.lower()}"
            
            tables[full_table_name].append({
                'name': col_name,
                'position': position,
                'data_type': dtype,
                'nullable': nullable == 'YES',
                'default': default,
                'comment': comment,
                'schema': schema,
                'database': database_name
            })
        
        print(f"  Found {len(tables)} tables with {sum(len(cols) for cols in tables.values())} columns")
        return dict(tables)
        
    except Exception as e:
        print(f"  Error querying {database_name}: {e}")
        return {}
    finally:
        cursor.close()

def extract_snowflake_inventory(account, user, role, warehouse, repo_name):
    """
    Extract complete inventory from Snowflake.
    """
    print(f"\n{'='*80}")
    print(f"Extracting inventory from Snowflake for {repo_name}")
    print(f"{'='*80}")
    
    conn = connect_to_snowflake(account, user, role, warehouse)
    
    # Query all three databases
    all_tables = {}
    
    for database in ['LANDING', 'SILVER', 'GOLD']:
        tables = get_all_columns_for_database(conn, database)
        all_tables.update(tables)
    
    conn.close()
    
    # Organize by layer
    by_layer = defaultdict(list)
    for table_name, columns in all_tables.items():
        # Parse layer from table name
        parts = table_name.split('__')
        if len(parts) >= 3:
            layer = parts[0]  # bronze/silver/gold
            domain = parts[1]
            table = '__'.join(parts[2:])
        else:
            layer = 'unknown'
            domain = 'unknown'
            table = table_name
        
        model_info = {
            'name': table_name,
            'layer': layer,
            'domain': domain,
            'table': table,
            'columns': columns,
            'column_count': len(columns),
            'database': columns[0]['database'] if columns else None,
            'schema': columns[0]['schema'] if columns else None
        }
        
        by_layer[layer].append(model_info)
    
    # Convert to regular dict for JSON serialization
    models_dict = {table_name: {
        'name': table_name,
        'layer': table_name.split('__')[0] if '__' in table_name else 'unknown',
        'domain': table_name.split('__')[1] if table_name.count('__') >= 2 else 'unknown',
        'table': '__'.join(table_name.split('__')[2:]) if table_name.count('__') >= 2 else table_name,
        'columns': columns,
        'column_count': len(columns),
        'database': columns[0]['database'] if columns else None,
        'schema': columns[0]['schema'] if columns else None
    } for table_name, columns in all_tables.items()}
    
    # Statistics
    stats = {
        'total_models': len(all_tables),
        'by_layer': {layer: len(models) for layer, models in by_layer.items()},
        'total_columns': sum(len(cols) for cols in all_tables.values())
    }
    
    print(f"\n{'='*80}")
    print("Statistics:")
    print(f"  Total tables: {stats['total_models']}")
    print(f"  Total columns: {stats['total_columns']}")
    print(f"  By layer:")
    for layer in sorted(stats['by_layer'].keys()):
        count = stats['by_layer'][layer]
        layer_columns = sum(len(m['columns']) for m in by_layer[layer])
        print(f"    {layer}: {count} tables, {layer_columns} columns")
    
    return {
        'repo_name': repo_name,
        'account': account,
        'models': models_dict,
        'by_layer': {k: v for k, v in by_layer.items()},
        'statistics': stats
    }

def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract dbt model columns from Snowflake')
    parser.add_argument('--account', required=True, help='Snowflake account name')
    parser.add_argument('--user', required=True, help='Snowflake username')
    parser.add_argument('--role', default='TRANSFORMER', help='Snowflake role')
    parser.add_argument('--warehouse', default='TRANSFORM_WH', help='Snowflake warehouse')
    parser.add_argument('--repo-name', required=True, help='Repository name (GXS/GXBank)')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Extract inventory
    inventory = extract_snowflake_inventory(
        account=args.account,
        user=args.user,
        role=args.role,
        warehouse=args.warehouse,
        repo_name=args.repo_name
    )
    
    # Save to file
    with open(args.output, 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"\n✓ Saved inventory to {args.output}")
    
    # Verify test case if GXS
    if 'GXS' in args.repo_name.upper():
        test_model = 'silver__core__casa_transactions'
        if test_model in inventory['models']:
            model = inventory['models'][test_model]
            print(f"\n✓ Verification: {test_model} has {model['column_count']} columns")
            print(f"  Columns: {', '.join([c['name'] for c in model['columns'][:10]])}...")
        else:
            print(f"\n⚠ Warning: {test_model} not found in Snowflake")

if __name__ == '__main__':
    main()

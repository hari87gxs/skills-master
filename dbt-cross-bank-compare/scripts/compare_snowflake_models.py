#!/usr/bin/env python3
"""
Deep column-level comparison of dbt models between GXS and GXBank.
Uses accurate Snowflake data extracted from information_schema.
"""

import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def load_inventory(file_path: str) -> Dict:
    """Load inventory JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_column_similarity(gxs_cols: List[Dict], gxbank_cols: List[Dict]) -> Dict:
    """
    Calculate column-level similarity between two models.
    Returns similarity metrics and detailed comparison.
    """
    gxs_col_names = {col['name'].upper() for col in gxs_cols}
    gxbank_col_names = {col['name'].upper() for col in gxbank_cols}
    
    common_cols = gxs_col_names & gxbank_col_names
    gxs_only_cols = gxs_col_names - gxbank_col_names
    gxbank_only_cols = gxbank_col_names - gxs_col_names
    
    total_unique_cols = len(gxs_col_names | gxbank_col_names)
    
    if total_unique_cols == 0:
        similarity_pct = 0
    else:
        similarity_pct = (len(common_cols) / total_unique_cols) * 100
    
    # Get data type comparison for common columns
    gxs_col_dict = {col['name'].upper(): col['data_type'] for col in gxs_cols}
    gxbank_col_dict = {col['name'].upper(): col['data_type'] for col in gxbank_cols}
    
    type_matches = 0
    type_mismatches = []
    
    for col_name in common_cols:
        gxs_type = gxs_col_dict.get(col_name, 'UNKNOWN')
        gxbank_type = gxbank_col_dict.get(col_name, 'UNKNOWN')
        if gxs_type == gxbank_type:
            type_matches += 1
        else:
            type_mismatches.append({
                'column': col_name,
                'gxs_type': gxs_type,
                'gxbank_type': gxbank_type
            })
    
    return {
        'similarity_pct': round(similarity_pct, 2),
        'gxs_col_count': len(gxs_col_names),
        'gxbank_col_count': len(gxbank_col_names),
        'common_col_count': len(common_cols),
        'gxs_only_col_count': len(gxs_only_cols),
        'gxbank_only_col_count': len(gxbank_only_cols),
        'common_cols': sorted(list(common_cols)),
        'gxs_only_cols': sorted(list(gxs_only_cols)),
        'gxbank_only_cols': sorted(list(gxbank_only_cols)),
        'type_matches': type_matches,
        'type_mismatches': type_mismatches
    }

def compare_models(gxs_inventory: Dict, gxbank_inventory: Dict) -> Dict:
    """
    Deep comparison of models between GXS and GXBank.
    Categorizes into: Identical, Similar, Divergent, and Bank-specific.
    """
    print(f"\n{'='*80}")
    print("DEEP MODEL COMPARISON - Column Level Analysis")
    print(f"{'='*80}\n")
    
    gxs_models = gxs_inventory['models']
    gxbank_models = gxbank_inventory['models']
    
    gxs_model_names = set(gxs_models.keys())
    gxbank_model_names = set(gxbank_models.keys())
    
    common_model_names = gxs_model_names & gxbank_model_names
    gxs_only_names = gxs_model_names - gxbank_model_names
    gxbank_only_names = gxbank_model_names - gxs_model_names
    
    print(f"Model overlap:")
    print(f"  Common models (same name): {len(common_model_names)}")
    print(f"  GXS-only models: {len(gxs_only_names)}")
    print(f"  GXBank-only models: {len(gxbank_only_names)}")
    print()
    
    # Categorize common models by similarity
    identical = []  # 100% match
    similar = []    # 70-99% match
    divergent = []  # <70% match
    
    print("Analyzing common models...")
    for model_name in sorted(common_model_names):
        gxs_model = gxs_models[model_name]
        gxbank_model = gxbank_models[model_name]
        
        comparison = calculate_column_similarity(
            gxs_model['columns'],
            gxbank_model['columns']
        )
        
        result = {
            'name': model_name,
            'layer': gxs_model['layer'],
            'domain': gxs_model['domain'],
            'table': gxs_model['table'],
            'comparison': comparison
        }
        
        similarity = comparison['similarity_pct']
        
        if similarity == 100.0:
            identical.append(result)
        elif similarity >= 70.0:
            similar.append(result)
        else:
            divergent.append(result)
    
    # Organize GXS-only and GXBank-only by layer
    gxs_only_by_layer = defaultdict(list)
    for model_name in gxs_only_names:
        model = gxs_models[model_name]
        gxs_only_by_layer[model['layer']].append({
            'name': model_name,
            'layer': model['layer'],
            'domain': model['domain'],
            'table': model['table'],
            'column_count': model['column_count'],
            'columns': [col['name'] for col in model['columns']]
        })
    
    gxbank_only_by_layer = defaultdict(list)
    for model_name in gxbank_only_names:
        model = gxbank_models[model_name]
        gxbank_only_by_layer[model['layer']].append({
            'name': model_name,
            'layer': model['layer'],
            'domain': model['domain'],
            'table': model['table'],
            'column_count': model['column_count'],
            'columns': [col['name'] for col in model['columns']]
        })
    
    # Sort by column count descending
    identical.sort(key=lambda x: x['comparison']['common_col_count'], reverse=True)
    similar.sort(key=lambda x: x['comparison']['common_col_count'], reverse=True)
    divergent.sort(key=lambda x: x['comparison']['common_col_count'], reverse=True)
    
    for layer in gxs_only_by_layer:
        gxs_only_by_layer[layer].sort(key=lambda x: x['column_count'], reverse=True)
    for layer in gxbank_only_by_layer:
        gxbank_only_by_layer[layer].sort(key=lambda x: x['column_count'], reverse=True)
    
    # Print summary
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Common Models Analysis:")
    print(f"  Identical (100% match): {len(identical)} models")
    print(f"  Similar (70-99% match): {len(similar)} models")
    print(f"  Divergent (<70% match): {len(divergent)} models")
    print()
    
    print(f"Bank-Specific Models:")
    print(f"  GXS-only models: {len(gxs_only_names)}")
    for layer in sorted(gxs_only_by_layer.keys()):
        models = gxs_only_by_layer[layer]
        total_cols = sum(m['column_count'] for m in models)
        print(f"    {layer}: {len(models)} models, {total_cols} columns")
    
    print(f"\n  GXBank-only models: {len(gxbank_only_names)}")
    for layer in sorted(gxbank_only_by_layer.keys()):
        models = gxbank_only_by_layer[layer]
        total_cols = sum(m['column_count'] for m in models)
        print(f"    {layer}: {len(models)} models, {total_cols} columns")
    
    return {
        'identical': identical,
        'similar': similar,
        'divergent': divergent,
        'gxs_only': dict(gxs_only_by_layer),
        'gxbank_only': dict(gxbank_only_by_layer),
        'summary': {
            'identical_count': len(identical),
            'similar_count': len(similar),
            'divergent_count': len(divergent),
            'gxs_only_count': len(gxs_only_names),
            'gxbank_only_count': len(gxbank_only_names),
            'common_models_count': len(common_model_names)
        }
    }

def main():
    """Main execution."""
    print("\nLoading inventories...")
    
    gxs_inventory = load_inventory('/tmp/gxs_inventory_snowflake.json')
    gxbank_inventory = load_inventory('/tmp/gxbank_inventory_snowflake.json')
    
    print(f"✓ Loaded GXS Bank: {gxs_inventory['statistics']['total_models']} models")
    print(f"✓ Loaded GXBank: {gxbank_inventory['statistics']['total_models']} models")
    
    # Run comparison
    results = compare_models(gxs_inventory, gxbank_inventory)
    
    # Save results
    output_file = '/tmp/comparison_results_snowflake.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Saved comparison results to {output_file}")
    print(f"\nReady to generate reports!")

if __name__ == '__main__':
    main()

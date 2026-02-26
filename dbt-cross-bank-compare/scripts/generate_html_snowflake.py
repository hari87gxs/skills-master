#!/usr/bin/env python3
"""
Generate HTML report from Snowflake comparison results.
Updated to work with the new comparison data structure.
"""

import json
from datetime import datetime
from collections import defaultdict

def generate_html_report(results_path: str, output_path: str):
    """Generate HTML report from Snowflake comparison results"""
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    summary = results['summary']
    
    # Process bank-specific models by layer
    gxs_only_by_layer = {}
    for layer, models in results['gxs_only'].items():
        total_cols = sum(m['column_count'] for m in models)
        gxs_only_by_layer[layer] = {
            'models': sorted(models, key=lambda x: x['column_count'], reverse=True),
            'total_cols': total_cols
        }
    
    gxbank_only_by_layer = {}
    for layer, models in results['gxbank_only'].items():
        total_cols = sum(m['column_count'] for m in models)
        gxbank_only_by_layer[layer] = {
            'models': sorted(models, key=lambda x: x['column_count'], reverse=True),
            'total_cols': total_cols
        }
    
    # Sort common models by column count
    identical = sorted(results['identical'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    similar = sorted(results['similar'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    divergent = sorted(results['divergent'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dbt Cross-Bank Model Comparison</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'IBM Plex Sans', sans-serif; 
            background: #0a1628; 
            color: #e8edf4; 
            line-height: 1.6; 
            padding: 20px; 
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center; padding: 40px 20px;
            background: linear-gradient(135deg, #0f1f3a 0%, #1a2942 100%);
            border-bottom: 3px solid #00d4ff;
            border-radius: 8px; margin-bottom: 40px;
        }}
        h1 {{ color: #00d4ff; font-size: 2.5em; margin-bottom: 10px; }}
        .subtitle {{ color: #a8b8d0; font-size: 1.1em; }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin: 30px 0;
        }}
        .stat-card {{
            background: #1a2942; padding: 20px; border-radius: 8px;
            border-left: 4px solid #00d4ff; text-align: center;
        }}
        .stat-value {{ font-size: 2.5em; font-weight: 700; color: #00ff88; }}
        .stat-label {{ color: #a8b8d0; font-size: 0.9em; margin-top: 5px; }}
        .section {{
            background: #0f1f3a; border: 1px solid #2a3f5f;
            border-radius: 8px; margin-bottom: 20px; overflow: hidden;
        }}
        .section-header {{
            padding: 20px 25px; background: #1a2942; cursor: pointer;
            display: flex; justify-content: space-between; align-items: center;
            transition: background 0.3s; user-select: none;
        }}
        .section-header:hover {{ background: #243550; }}
        .section-title {{ font-size: 1.3em; font-weight: 600; }}
        .section-count {{
            background: #00d4ff; color: #0a1628;
            padding: 5px 15px; border-radius: 20px; font-weight: 600;
            font-family: 'IBM Plex Mono', monospace;
        }}
        .section-count.success {{ background: #00ff88; }}
        .section-count.warning {{ background: #ffaa00; }}
        .section-count.danger {{ background: #ff4466; }}
        .expand-icon {{
            color: #00d4ff; font-size: 1.2em;
            transition: transform 0.3s;
        }}
        .section-header.expanded .expand-icon {{ transform: rotate(90deg); }}
        .section-content {{
            max-height: 0; overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .section-content.show {{
            max-height: 100000px;
            transition: max-height 0.5s ease-in;
        }}
        .section-body {{
            padding: 25px; max-height: 800px; overflow-y: auto;
        }}
        .section-body::-webkit-scrollbar {{ width: 10px; }}
        .section-body::-webkit-scrollbar-track {{ background: #0f1f3a; }}
        .section-body::-webkit-scrollbar-thumb {{ background: #00d4ff; border-radius: 5px; }}
        .model-detail {{
            background: #1a2942; padding: 15px; border-radius: 6px;
            margin-bottom: 15px; border-left: 3px solid #00d4ff;
        }}
        .model-header {{
            display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 10px;
        }}
        .model-name {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.1em; font-weight: 600; color: #00d4ff;
        }}
        .model-meta {{ color: #6b7a94; font-size: 0.9em; }}
        .comparison-stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px; margin: 10px 0;
        }}
        .stat-item {{
            background: #0f1f3a; padding: 10px; border-radius: 4px;
            text-align: center;
        }}
        .stat-item-value {{ font-size: 1.5em; font-weight: 600; color: #00ff88; }}
        .stat-item-label {{ color: #a8b8d0; font-size: 0.85em; }}
        .column-list {{
            background: #0f1f3a; padding: 10px; border-radius: 4px;
            font-family: 'IBM Plex Mono', monospace; font-size: 0.85em;
            max-height: 200px; overflow-y: auto;
        }}
        .column-list-header {{ color: #00d4ff; font-weight: 600; margin-bottom: 5px; }}
        .column-item {{ color: #a8b8d0; padding: 2px 0; }}
        .badge {{
            display: inline-block; padding: 3px 8px; border-radius: 3px;
            font-size: 0.75em; font-weight: 600; margin-right: 5px;
        }}
        .badge.silver {{ background: #c0c0c0; color: #000; }}
        .badge.gold {{ background: #ffd700; color: #000; }}
        .badge.bronze, .badge.landing {{ background: #cd7f32; color: #fff; }}
        .search-box {{
            width: 100%; padding: 10px; background: #0f1f3a;
            border: 1px solid #2a3f5f; border-radius: 4px;
            color: #e8edf4; margin-bottom: 15px;
            font-family: 'IBM Plex Mono', monospace;
        }}
        .layer-section {{
            background: #1a2942; padding: 15px; border-radius: 6px;
            margin-bottom: 15px;
        }}
        .layer-header {{
            display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 10px;
        }}
        .layer-title {{ color: #00d4ff; font-size: 1.1em; font-weight: 600; }}
        .layer-stats {{ color: #a8b8d0; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏦 dbt Cross-Bank Model Comparison</h1>
            <p class="subtitle">GXS Bank vs GXBank | Column-Level Analysis</p>
            <p class="subtitle">Data Source: Snowflake information_schema | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary['common_models_count']}</div>
                <div class="stat-label">Common Models</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #00ff88;">{summary['identical_count']}</div>
                <div class="stat-label">Identical (100%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ffaa00;">{summary['similar_count']}</div>
                <div class="stat-label">Similar (70-99%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ff4466;">{summary['divergent_count']}</div>
                <div class="stat-label">Divergent (<70%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['gxs_only_count']}</div>
                <div class="stat-label">GXS-Only</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['gxbank_only_count']}</div>
                <div class="stat-label">GXBank-Only</div>
            </div>
        </div>
'''
    
    # Identical Models Section
    html += generate_common_models_section(
        "✅ Identical Models (100% Match)",
        "Ready for immediate homogenization",
        identical,
        "success"
    )
    
    # Similar Models Section
    html += generate_common_models_section(
        "⚠️ Similar Models (70-99% Match)",
        "Low effort to align - minor column differences",
        similar,
        "warning"
    )
    
    # Divergent Models Section
    html += generate_common_models_section(
        "❌ Divergent Models (<70% Match)",
        "Requires business decisions and significant changes",
        divergent,
        "danger"
    )
    
    # GXS-Only Models Section
    html += generate_bank_specific_section(
        "GXS Bank Only",
        gxs_only_by_layer,
        summary['gxs_only_count']
    )
    
    # GXBank-Only Models Section
    html += generate_bank_specific_section(
        "GXBank Only",
        gxbank_only_by_layer,
        summary['gxbank_only_count']
    )
    
    html += '''
    </div>
    <script>
        function toggleSection(id) {
            const header = document.getElementById(id + '-header');
            const content = document.getElementById(id + '-content');
            header.classList.toggle('expanded');
            content.classList.toggle('show');
        }
        
        function searchModels(inputId, containerId) {
            const input = document.getElementById(inputId);
            const filter = input.value.toLowerCase();
            const container = document.getElementById(containerId);
            const models = container.getElementsByClassName('model-detail');
            
            for (let model of models) {
                const text = model.textContent.toLowerCase();
                model.style.display = text.includes(filter) ? '' : 'none';
            }
        }
    </script>
</body>
</html>
'''
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ HTML report generated: {output_path}")

def generate_common_models_section(title, description, models, badge_class):
    """Generate HTML for common models section (identical/similar/divergent)"""
    
    html = f'''
        <div class="section">
            <div class="section-header" id="{badge_class}-header" onclick="toggleSection('{badge_class}')">
                <div>
                    <div class="section-title">{title}</div>
                    <div style="color: #6b7a94; font-size: 0.9em; margin-top: 5px;">{description}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="section-count {badge_class}">{len(models)}</span>
                    <span class="expand-icon">▶</span>
                </div>
            </div>
            <div class="section-content" id="{badge_class}-content">
                <div class="section-body">
                    <input type="text" class="search-box" id="{badge_class}-search" 
                           placeholder="Search models..." 
                           onkeyup="searchModels('{badge_class}-search', '{badge_class}-models')">
                    <div id="{badge_class}-models">
'''
    
    for model in models:
        comp = model['comparison']
        similarity = comp['similarity_pct']
        
        html += f'''
                        <div class="model-detail">
                            <div class="model-header">
                                <div>
                                    <div class="model-name">{model['name']}</div>
                                    <div class="model-meta">
                                        <span class="badge {model['layer']}">{model['layer'].upper()}</span>
                                        {model['domain']} • {model['table']}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 1.5em; font-weight: 600; color: #00ff88;">
                                        {similarity:.1f}%
                                    </div>
                                    <div style="color: #6b7a94; font-size: 0.85em;">similarity</div>
                                </div>
                            </div>
                            
                            <div class="comparison-stats">
                                <div class="stat-item">
                                    <div class="stat-item-value">{comp['gxs_col_count']}</div>
                                    <div class="stat-item-label">GXS Columns</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-item-value">{comp['gxbank_col_count']}</div>
                                    <div class="stat-item-label">GXBank Columns</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-item-value">{comp['common_col_count']}</div>
                                    <div class="stat-item-label">Common</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-item-value">{comp['gxs_only_col_count']}</div>
                                    <div class="stat-item-label">GXS Only</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-item-value">{comp['gxbank_only_col_count']}</div>
                                    <div class="stat-item-label">GXBank Only</div>
                                </div>
                            </div>
'''
        
        # Show column differences for similar and divergent
        if comp['gxs_only_col_count'] > 0 or comp['gxbank_only_col_count'] > 0:
            html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">'
            
            if comp['gxs_only_col_count'] > 0:
                cols_preview = ', '.join(comp['gxs_only_cols'][:5])
                if len(comp['gxs_only_cols']) > 5:
                    cols_preview += f"... (+{len(comp['gxs_only_cols'])-5} more)"
                html += f'''
                <div class="column-list">
                    <div class="column-list-header">GXS-Only Columns ({comp['gxs_only_col_count']})</div>
                    <div style="color: #a8b8d0;">{cols_preview}</div>
                </div>
'''
            
            if comp['gxbank_only_col_count'] > 0:
                cols_preview = ', '.join(comp['gxbank_only_cols'][:5])
                if len(comp['gxbank_only_cols']) > 5:
                    cols_preview += f"... (+{len(comp['gxbank_only_cols'])-5} more)"
                html += f'''
                <div class="column-list">
                    <div class="column-list-header">GXBank-Only Columns ({comp['gxbank_only_col_count']})</div>
                    <div style="color: #a8b8d0;">{cols_preview}</div>
                </div>
'''
            html += '</div>'
        
        html += '</div>\n'
    
    html += '''
                    </div>
                </div>
            </div>
        </div>
'''
    return html

def generate_bank_specific_section(bank_name, models_by_layer, total_count):
    """Generate HTML for bank-specific models section"""
    
    section_id = bank_name.lower().replace(' ', '-')
    
    html = f'''
        <div class="section">
            <div class="section-header" id="{section_id}-header" onclick="toggleSection('{section_id}')">
                <div>
                    <div class="section-title">🏦 {bank_name} Models</div>
                    <div style="color: #6b7a94; font-size: 0.9em; margin-top: 5px;">
                        Models that exist only in {bank_name}
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="section-count info">{total_count}</span>
                    <span class="expand-icon">▶</span>
                </div>
            </div>
            <div class="section-content" id="{section_id}-content">
                <div class="section-body">
'''
    
    for layer in sorted(models_by_layer.keys()):
        data = models_by_layer[layer]
        models = data['models']
        total_cols = data['total_cols']
        
        html += f'''
                    <div class="layer-section">
                        <div class="layer-header">
                            <div>
                                <span class="badge {layer}">{layer.upper()}</span>
                                <span class="layer-title">{layer.capitalize()} Layer</span>
                            </div>
                            <div class="layer-stats">
                                {len(models)} models • {total_cols:,} columns
                            </div>
                        </div>
                        <div style="max-height: 300px; overflow-y: auto;">
'''
        
        for model in models[:50]:  # Show top 50 per layer
            html += f'''
                            <div class="model-detail">
                                <div class="model-header">
                                    <div>
                                        <div class="model-name">{model['name']}</div>
                                        <div class="model-meta">{model['domain']} • {model['table']}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.2em; font-weight: 600; color: #00d4ff;">
                                            {model['column_count']}
                                        </div>
                                        <div style="color: #6b7a94; font-size: 0.85em;">columns</div>
                                    </div>
                                </div>
                            </div>
'''
        
        if len(models) > 50:
            html += f'<div style="color: #6b7a94; text-align: center; padding: 10px;">... and {len(models)-50} more models</div>'
        
        html += '''
                        </div>
                    </div>
'''
    
    html += '''
                </div>
            </div>
        </div>
'''
    return html

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 generate_html_snowflake.py <comparison_results.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = '/Users/harikrishnan.r/.agent/reports/dbt-cross-bank-comparison-snowflake.html'
    
    generate_html_report(results_file, output_file)

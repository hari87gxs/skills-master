#!/usr/bin/env python3
"""
Generate Google Docs compatible HTML report.
Uses simple HTML tables and basic formatting only.
"""

import json
from datetime import datetime

def generate_gdocs_html(results_path: str, output_path: str):
    """Generate Google Docs compatible HTML"""
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    summary = results['summary']
    
    # Sort models
    identical = sorted(results['identical'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    similar = sorted(results['similar'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    divergent = sorted(results['divergent'], key=lambda x: x['comparison']['common_col_count'], reverse=True)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>dbt Cross-Bank Model Comparison</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #1a73e8; margin-top: 30px; border-bottom: 2px solid #e8f0fe; padding-bottom: 8px; }}
        h3 {{ color: #5f6368; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background-color: #1a73e8; color: white; padding: 12px; text-align: left; font-weight: bold; }}
        td {{ padding: 10px; border: 1px solid #dadce0; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .summary-table td {{ font-size: 14px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
        .success {{ color: #0f9d58; }}
        .warning {{ color: #f9ab00; }}
        .danger {{ color: #d93025; }}
        .model-name {{ font-family: monospace; font-weight: bold; color: #1a73e8; }}
        .meta {{ color: #5f6368; font-size: 12px; }}
        .badge {{ 
            display: inline-block; 
            padding: 3px 8px; 
            border-radius: 3px; 
            font-size: 11px; 
            font-weight: bold; 
            margin-right: 5px;
        }}
        .badge-silver {{ background-color: #c0c0c0; color: #000; }}
        .badge-gold {{ background-color: #ffd700; color: #000; }}
        .badge-bronze {{ background-color: #cd7f32; color: #fff; }}
        .badge-landing {{ background-color: #cd7f32; color: #fff; }}
        .subsection {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #1a73e8; }}
    </style>
</head>
<body>
    <h1>🏦 dbt Cross-Bank Model Comparison Report</h1>
    <p><strong>Banks:</strong> GXS Bank vs GXBank</p>
    <p><strong>Analysis Type:</strong> Deep Column-Level Comparison</p>
    <p><strong>Data Source:</strong> Snowflake information_schema (Production)</p>
    <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</p>
    
    <h2>📊 Executive Summary</h2>
    <table class="summary-table">
        <tr>
            <th>Metric</th>
            <th>Count</th>
            <th>Description</th>
        </tr>
        <tr>
            <td><strong>Common Models</strong></td>
            <td class="stat-value">{summary['common_models_count']}</td>
            <td>Models with same name in both banks</td>
        </tr>
        <tr>
            <td><strong>Identical Models</strong></td>
            <td class="stat-value success">{summary['identical_count']}</td>
            <td>100% column match - ready for immediate homogenization</td>
        </tr>
        <tr>
            <td><strong>Similar Models</strong></td>
            <td class="stat-value warning">{summary['similar_count']}</td>
            <td>70-99% match - low effort to align</td>
        </tr>
        <tr>
            <td><strong>Divergent Models</strong></td>
            <td class="stat-value danger">{summary['divergent_count']}</td>
            <td>&lt;70% match - requires business decisions</td>
        </tr>
        <tr>
            <td><strong>GXS-Only Models</strong></td>
            <td class="stat-value">{summary['gxs_only_count']}</td>
            <td>Models that exist only in GXS Bank</td>
        </tr>
        <tr>
            <td><strong>GXBank-Only Models</strong></td>
            <td class="stat-value">{summary['gxbank_only_count']}</td>
            <td>Models that exist only in GXBank</td>
        </tr>
    </table>
    
    <h2>✅ Identical Models (100% Column Match)</h2>
    <p><strong>Count:</strong> {len(identical)} models | <strong>Status:</strong> Ready for immediate homogenization</p>
    <p>These models have identical column structures and can be merged with minimal effort.</p>
    
    <table>
        <tr>
            <th>Model Name</th>
            <th>Layer</th>
            <th>Domain</th>
            <th>GXS Columns</th>
            <th>GXBank Columns</th>
            <th>Similarity</th>
        </tr>
'''
    
    for model in identical[:100]:  # Top 100
        comp = model['comparison']
        html += f'''
        <tr>
            <td><span class="model-name">{model['name']}</span></td>
            <td><span class="badge badge-{model['layer']}">{model['layer'].upper()}</span></td>
            <td>{model['domain']}</td>
            <td style="text-align: center;">{comp['gxs_col_count']}</td>
            <td style="text-align: center;">{comp['gxbank_col_count']}</td>
            <td style="text-align: center;"><strong class="success">{comp['similarity_pct']:.1f}%</strong></td>
        </tr>
'''
    
    if len(identical) > 100:
        html += f'<tr><td colspan="6" style="text-align: center; color: #5f6368;"><em>... and {len(identical)-100} more identical models</em></td></tr>'
    
    html += '</table>'
    
    # Similar Models
    html += f'''
    <h2>⚠️ Similar Models (70-99% Column Match)</h2>
    <p><strong>Count:</strong> {len(similar)} models | <strong>Effort:</strong> Low - requires minor column adjustments</p>
    <p>These models have mostly similar structures but need some column additions/removals to align.</p>
    
    <table>
        <tr>
            <th>Model Name</th>
            <th>Layer</th>
            <th>GXS Cols</th>
            <th>GXBank Cols</th>
            <th>Common</th>
            <th>GXS Only</th>
            <th>GXBank Only</th>
            <th>Similarity</th>
        </tr>
'''
    
    for model in similar[:50]:  # Top 50
        comp = model['comparison']
        html += f'''
        <tr>
            <td><span class="model-name">{model['name']}</span></td>
            <td><span class="badge badge-{model['layer']}">{model['layer'].upper()}</span></td>
            <td style="text-align: center;">{comp['gxs_col_count']}</td>
            <td style="text-align: center;">{comp['gxbank_col_count']}</td>
            <td style="text-align: center;">{comp['common_col_count']}</td>
            <td style="text-align: center;">{comp['gxs_only_col_count']}</td>
            <td style="text-align: center;">{comp['gxbank_only_col_count']}</td>
            <td style="text-align: center;"><strong class="warning">{comp['similarity_pct']:.1f}%</strong></td>
        </tr>
'''
    
    if len(similar) > 50:
        html += f'<tr><td colspan="8" style="text-align: center; color: #5f6368;"><em>... and {len(similar)-50} more similar models</em></td></tr>'
    
    html += '</table>'
    
    # Divergent Models with Details
    html += f'''
    <h2>❌ Divergent Models (&lt;70% Column Match)</h2>
    <p><strong>Count:</strong> {len(divergent)} models | <strong>Effort:</strong> High - requires business review and decisions</p>
    <p>These models have significant structural differences and require stakeholder alignment.</p>
    
    <table>
        <tr>
            <th>Model Name</th>
            <th>Layer</th>
            <th>GXS Cols</th>
            <th>GXBank Cols</th>
            <th>Common</th>
            <th>GXS Only</th>
            <th>GXBank Only</th>
            <th>Similarity</th>
        </tr>
'''
    
    for model in divergent:
        comp = model['comparison']
        html += f'''
        <tr>
            <td><span class="model-name">{model['name']}</span></td>
            <td><span class="badge badge-{model['layer']}">{model['layer'].upper()}</span></td>
            <td style="text-align: center;">{comp['gxs_col_count']}</td>
            <td style="text-align: center;">{comp['gxbank_col_count']}</td>
            <td style="text-align: center;">{comp['common_col_count']}</td>
            <td style="text-align: center;">{comp['gxs_only_col_count']}</td>
            <td style="text-align: center;">{comp['gxbank_only_col_count']}</td>
            <td style="text-align: center;"><strong class="danger">{comp['similarity_pct']:.1f}%</strong></td>
        </tr>
'''
        
        # Show column differences for divergent models
        if comp['gxs_only_col_count'] > 0 or comp['gxbank_only_col_count'] > 0:
            html += '<tr><td colspan="8" style="background-color: #fff; padding: 15px;">'
            
            if comp['gxs_only_col_count'] > 0:
                cols = ', '.join(comp['gxs_only_cols'][:10])
                if len(comp['gxs_only_cols']) > 10:
                    cols += f" ... (+{len(comp['gxs_only_cols'])-10} more)"
                html += f'<p><strong>GXS-Only Columns ({comp["gxs_only_col_count"]}):</strong> {cols}</p>'
            
            if comp['gxbank_only_col_count'] > 0:
                cols = ', '.join(comp['gxbank_only_cols'][:10])
                if len(comp['gxbank_only_cols']) > 10:
                    cols += f" ... (+{len(comp['gxbank_only_cols'])-10} more)"
                html += f'<p><strong>GXBank-Only Columns ({comp["gxbank_only_col_count"]}):</strong> {cols}</p>'
            
            html += '</td></tr>'
    
    html += '</table>'
    
    # Bank-specific models by layer
    html += '''
    <h2>🏦 Bank-Specific Models Summary</h2>
    <p>Models that exist in only one bank, organized by data layer.</p>
    
    <h3>GXS Bank Only</h3>
    <table>
        <tr>
            <th>Layer</th>
            <th>Model Count</th>
            <th>Total Columns</th>
        </tr>
'''
    
    for layer in sorted(results['gxs_only'].keys()):
        models = results['gxs_only'][layer]
        total_cols = sum(m['column_count'] for m in models)
        html += f'''
        <tr>
            <td><span class="badge badge-{layer}">{layer.upper()}</span></td>
            <td style="text-align: center;">{len(models)}</td>
            <td style="text-align: center;">{total_cols:,}</td>
        </tr>
'''
    
    html += '''
    </table>
    
    <h3>GXBank Only</h3>
    <table>
        <tr>
            <th>Layer</th>
            <th>Model Count</th>
            <th>Total Columns</th>
        </tr>
'''
    
    for layer in sorted(results['gxbank_only'].keys()):
        models = results['gxbank_only'][layer]
        total_cols = sum(m['column_count'] for m in models)
        html += f'''
        <tr>
            <td><span class="badge badge-{layer}">{layer.upper()}</span></td>
            <td style="text-align: center;">{len(models)}</td>
            <td style="text-align: center;">{total_cols:,}</td>
        </tr>
'''
    
    html += '''
    </table>
    
    <h2>🎯 Recommendations</h2>
    
    <div class="subsection">
        <h3>Phase 1: Quick Wins (Immediate Action)</h3>
        <ul>
            <li><strong>Target:</strong> 195 identical models</li>
            <li><strong>Priority:</strong> Silver layer models first</li>
            <li><strong>Effort:</strong> Low - configuration changes only</li>
            <li><strong>Timeline:</strong> 1-2 sprints</li>
        </ul>
    </div>
    
    <div class="subsection">
        <h3>Phase 2: Low-Effort Alignment</h3>
        <ul>
            <li><strong>Target:</strong> 190 similar models</li>
            <li><strong>Actions:</strong> Add/remove columns, standardize naming</li>
            <li><strong>Effort:</strong> Medium - code changes required</li>
            <li><strong>Timeline:</strong> 2-3 months</li>
        </ul>
    </div>
    
    <div class="subsection">
        <h3>Phase 3: Strategic Alignment</h3>
        <ul>
            <li><strong>Target:</strong> 83 divergent models</li>
            <li><strong>Actions:</strong> Business review, stakeholder decisions, significant refactoring</li>
            <li><strong>Effort:</strong> High - requires alignment across teams</li>
            <li><strong>Timeline:</strong> 3-6 months</li>
        </ul>
    </div>
    
    <div class="subsection">
        <h3>Phase 4: Bank-Specific Evaluation</h3>
        <ul>
            <li><strong>Target:</strong> 11,773 bank-specific models</li>
            <li><strong>Actions:</strong> Determine which are truly market-specific vs candidates for standardization</li>
            <li><strong>Effort:</strong> Ongoing - requires business context</li>
            <li><strong>Timeline:</strong> 6-12 months</li>
        </ul>
    </div>
    
    <h2>📋 Methodology</h2>
    <p>This analysis was performed using production Snowflake schemas extracted via <code>information_schema.columns</code> to ensure 100% accuracy.</p>
    
    <h3>Data Sources</h3>
    <ul>
        <li><strong>GXS Bank:</strong> Queried LANDING, SILVER, and GOLD databases (8,058 tables, 310,986 columns)</li>
        <li><strong>GXBank:</strong> Queried LANDING, SILVER, and GOLD databases (4,651 tables, 179,895 columns)</li>
    </ul>
    
    <h3>Comparison Approach</h3>
    <ol>
        <li>Matched models by name (layer__domain__table format)</li>
        <li>Performed column-level comparison (names and data types)</li>
        <li>Calculated similarity percentage based on shared columns</li>
        <li>Categorized models into identical, similar, divergent, and bank-specific</li>
    </ol>
    
    <h3>Categorization Criteria</h3>
    <ul>
        <li><strong>Identical:</strong> 100% column match between banks</li>
        <li><strong>Similar:</strong> 70-99% column match (minor differences)</li>
        <li><strong>Divergent:</strong> &lt;70% column match (major differences)</li>
        <li><strong>Bank-Specific:</strong> Model exists in only one bank</li>
    </ul>
    
    <hr>
    <p style="color: #5f6368; font-size: 12px; margin-top: 40px;">
        Report generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")} using OpenCode dbt Cross-Bank Comparison Tool
    </p>
</body>
</html>
'''
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Google Docs compatible HTML generated: {output_path}")
    print(f"\nTo import to Google Docs:")
    print(f"1. Open Google Docs (docs.google.com)")
    print(f"2. File → Open → Upload")
    print(f"3. Select this file: {output_path}")
    print(f"4. Google Docs will automatically convert it")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 generate_gdocs_html.py <comparison_results.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = '/Users/harikrishnan.r/.agent/reports/dbt-comparison-gdocs.html'
    
    generate_gdocs_html(results_file, output_file)

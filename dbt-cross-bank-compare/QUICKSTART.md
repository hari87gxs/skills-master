# Quick Start Guide

Get started with the dbt Cross-Bank Model Comparison Tool in 3 steps.

## Prerequisites

- Python 3.7+
- Snowflake access for both banks
- Browser-based SSO enabled

## Installation

```bash
pip3 install snowflake-connector-python
```

## Step-by-Step

### 1. Extract from Snowflake (Bank A)

```bash
python3 scripts/extract_from_snowflake.py \
  --account your-account-prod \
  --user your.email@company.com \
  --role TRANSFORMER \
  --warehouse TRANSFORM_WH \
  --repo-name "Bank A" \
  --output /tmp/bankA_inventory.json
```

**Authentication:** A browser window will open - complete SSO login.

**Time:** ~2-5 minutes depending on schema size

### 2. Extract from Snowflake (Bank B)

```bash
python3 scripts/extract_from_snowflake.py \
  --account bankb-account-prod \
  --user your.email@company.com \
  --role TRANSFORMER \
  --warehouse TRANSFORM_WH \
  --repo-name "Bank B" \
  --output /tmp/bankB_inventory.json
```

### 3. Compare Models

Edit `scripts/compare_snowflake_models.py` to point to your inventory files:

```python
# Line 265-266
gxs_inventory = load_inventory('/tmp/bankA_inventory.json')
gxbank_inventory = load_inventory('/tmp/bankB_inventory.json')
```

Then run:

```bash
python3 scripts/compare_snowflake_models.py
```

Output: `/tmp/comparison_results_snowflake.json`

### 4. Generate Reports

#### Interactive HTML
```bash
python3 scripts/generate_html_snowflake.py /tmp/comparison_results_snowflake.json
```

Output: `~/.agent/reports/dbt-cross-bank-comparison-snowflake.html`

Open in browser to explore!

#### Google Docs HTML
```bash
python3 scripts/generate_gdocs_html.py /tmp/comparison_results_snowflake.json
```

Output: `~/.agent/reports/dbt-comparison-gdocs.html`

Upload to Google Docs for easy sharing.

## Expected Results

After running, you'll see:

```
Common Models: 468
├─ Identical (100%): 195 ✅ Ready to homogenize
├─ Similar (70-99%): 190 ⚠️ Low effort
└─ Divergent (<70%): 83 ❌ Needs review

Bank-Specific:
├─ Bank A-only: 7,590
└─ Bank B-only: 4,183
```

## Next Steps

1. Open the interactive HTML report
2. Review identical models for quick wins
3. Analyze similar models for alignment opportunities
4. Schedule business review for divergent models
5. Evaluate bank-specific models

## Troubleshooting

**Issue:** Browser doesn't open for authentication  
**Fix:** Check Snowflake SSO is enabled for your account

**Issue:** Permission denied error  
**Fix:** Verify you have USAGE privilege on databases

**Issue:** Timeout errors  
**Fix:** Increase timeout in `extract_from_snowflake.py` line 54

## Support

Questions? Create an issue in the GitHub repository.

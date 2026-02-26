# Quick Start Guide: dbt Mapping Documentation Generator

Get up and running with the dbt Mapping Doc Generator in 5 minutes.

## Prerequisites

1. **Python 3.7+** installed
2. **Snowflake account access** with browser-based SSO
3. **dbt repository** cloned locally
4. **Network access** to Snowflake

## Installation

### Step 1: Install Python Dependencies

```bash
pip3 install snowflake-connector-python pyyaml sqlparse
```

### Step 2: Clone/Download This Tool

```bash
cd ~/skills-master
git pull  # If already cloned
```

## Basic Usage

### Generate Mapping Doc for a Single Model

```bash
python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa \
  --repo /path/to/your/dbt-repo \
  --sf-account your-snowflake-account \
  --sf-user your.email@company.com \
  --sf-role TRANSFORMER \
  --sf-warehouse TRANSFORM_WH \
  --output mapping_casa.csv
```

**What happens:**
1. Browser window opens for Snowflake SSO authentication
2. Script analyzes the dbt model SQL file
3. Extracts column lineage and transformations
4. Pulls metadata from Snowflake
5. Generates CSV file ready for Google Sheets

### Example: GXS Bank Model

```bash
python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa_transactions \
  --repo ~/projects/digibank-transformer \
  --sf-account gxs-prod \
  --sf-user your.email@grab.com \
  --sf-role TRANSFORMER \
  --sf-warehouse TRANSFORM_WH \
  --output ~/mapping_docs/casa_transactions.csv
```

### Example: GXBank Model

```bash
python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa \
  --repo ~/projects/dbmy-transformer \
  --sf-account $(cat ~/.gxbank_snowflake_account) \
  --sf-user your.email@gxbank.com \
  --sf-role TRANSFORMER \
  --sf-warehouse TRANSFORM_WH \
  --output ~/mapping_docs/gxbank_casa.csv
```

## Output Format

The generated CSV includes these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Table Name** | Target model name | `SILVER.CORE.CASA` |
| **Column Name** | Output column | `account_id` |
| **Logical Column Name** | Business-friendly name | `Account ID` |
| **Column Description** | From schema.yml | `Unique account identifier` |
| **Table Description** | Model-level docs | `Core CASA account details` |
| **R3/R3+** | Direct (R3) or Transformed (R3+) | `R3+` |
| **Value** | Transformation logic | `UPPER(TRIM(source.acct_id))` |
| **Remarks** | Additional context | `Normalized to uppercase` |
| **Queries** | Questions/issues | `Confirm normalization rules` |
| **Query team** | Who to ask | `Core Banking Team` |
| **Comment** | Analyst notes | `Added in v2.3` |
| **Source Team** | Data owner | `Accounts Service Team` |
| **Upstream Table Name** | Source table | `BRONZE.CORE_ACCOUNTS.CUSTOMER` |
| **Upstream Column Name** | Source column | `acct_id` |
| **Additional Comments** | Extra notes | `Migrated from legacy system` |

## Common Use Cases

### 1. Document a New Model

```bash
# After creating a new dbt model, generate its mapping doc
python3 scripts/generate_mapping_doc.py \
  --model silver__payments__transactions \
  --repo ~/dbt-repo \
  --sf-account prod-account \
  --sf-user user@company.com \
  --output new_model_mapping.csv
```

### 2. Update Existing Documentation

```bash
# After modifying a model, regenerate its docs
python3 scripts/generate_mapping_doc.py \
  --model silver__core__customers \
  --repo ~/dbt-repo \
  --sf-account prod-account \
  --sf-user user@company.com \
  --output updated_customer_mapping.csv
```

### 3. Audit Silver Layer Models

```bash
# Generate docs for multiple silver models
for model in silver__core__casa silver__core__customers silver__core__transactions; do
  python3 scripts/generate_mapping_doc.py \
    --model $model \
    --repo ~/dbt-repo \
    --sf-account prod-account \
    --sf-user user@company.com \
    --output "mappings/${model}.csv"
done
```

## Import to Google Sheets

### Method 1: Direct Upload
1. Open Google Sheets
2. Go to **File > Import**
3. Upload the CSV file
4. Choose **Replace spreadsheet** or **Insert new sheet**
5. Click **Import data**

### Method 2: Drag and Drop
1. Open Google Drive
2. Drag the CSV file to upload
3. Right-click > **Open with > Google Sheets**

### Method 3: Command Line (with gdrive CLI)
```bash
# Install gdrive CLI first
gdrive upload --parent <folder-id> mapping_casa.csv
```

## Troubleshooting

### Browser Authentication Not Working

**Problem:** Browser window doesn't open for Snowflake SSO

**Solution:**
```bash
# Check if you can manually access Snowflake
open https://your-account.snowflakecomputing.com

# Try with explicit authenticator
python3 scripts/generate_mapping_doc.py \
  --model your_model \
  --repo ~/dbt-repo \
  --sf-account your-account \
  --sf-user your.email@company.com \
  --sf-authenticator externalbrowser
```

### Model Not Found

**Problem:** Error: "Model file not found"

**Solution:**
```bash
# Verify model exists in repo
find ~/dbt-repo/models -name "*your_model*"

# Use exact model name (without .sql extension)
python3 scripts/generate_mapping_doc.py --model silver__core__casa ...
```

### Missing Snowflake Table

**Problem:** Warning: "Table not found in Snowflake"

**Solution:**
```bash
# Ensure model has been run in dbt
dbt run --select your_model

# Or generate docs without Snowflake metadata
# (script will still parse SQL and schema.yml)
```

### Empty Output CSV

**Problem:** CSV is generated but has no data

**Possible causes:**
1. Model SQL file is empty or invalid
2. No columns found in the model
3. Insufficient Snowflake permissions

**Solution:**
```bash
# Check model SQL file
cat ~/dbt-repo/models/path/to/your_model.sql

# Verify Snowflake access
snowsql -a your-account -u your.email@company.com \
  -q "SELECT * FROM INFORMATION_SCHEMA.COLUMNS LIMIT 1;"
```

### CSV Formatting Issues in Google Sheets

**Problem:** Columns not aligned properly

**Solution:**
1. When importing, choose **Comma** as separator
2. Set **UTF-8** encoding
3. Check **Detect automatically** for data types

## Advanced Usage

### Custom Output Directory

```bash
# Organize outputs by layer
mkdir -p ~/mapping_docs/{bronze,silver,gold}

python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa \
  --repo ~/dbt-repo \
  --sf-account prod \
  --sf-user user@company.com \
  --output ~/mapping_docs/silver/casa.csv
```

### Process Multiple Models

Create a simple bash script:

```bash
#!/bin/bash
# generate_all_mappings.sh

REPO_PATH=~/dbt-repo
SF_ACCOUNT=your-account
SF_USER=your.email@company.com
OUTPUT_DIR=~/mapping_docs

MODELS=(
  "silver__core__casa"
  "silver__core__customers"
  "silver__core__transactions"
  "silver__payments__transactions"
)

for model in "${MODELS[@]}"; do
  echo "Processing $model..."
  python3 scripts/generate_mapping_doc.py \
    --model "$model" \
    --repo "$REPO_PATH" \
    --sf-account "$SF_ACCOUNT" \
    --sf-user "$SF_USER" \
    --output "$OUTPUT_DIR/${model}.csv"
done

echo "Done! Generated ${#MODELS[@]} mapping docs"
```

### Environment Variables

```bash
# Set these in your ~/.zshrc or ~/.bashrc
export DBT_REPO_PATH=~/projects/dbt-repo
export SNOWFLAKE_ACCOUNT=your-account
export SNOWFLAKE_USER=your.email@company.com
export SNOWFLAKE_ROLE=TRANSFORMER
export SNOWFLAKE_WAREHOUSE=TRANSFORM_WH

# Then use shorter commands
python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa \
  --repo $DBT_REPO_PATH \
  --sf-account $SNOWFLAKE_ACCOUNT \
  --sf-user $SNOWFLAKE_USER \
  --sf-role $SNOWFLAKE_ROLE \
  --sf-warehouse $SNOWFLAKE_WAREHOUSE \
  --output mapping_casa.csv
```

## Next Steps

1. **Review the README.md** for detailed architecture and design decisions
2. **Customize the script** if you need additional columns or logic
3. **Integrate with CI/CD** to auto-generate docs on model changes
4. **Share feedback** on what works well and what could be improved

## Support

For issues or questions:
1. Check the main **README.md** for detailed documentation
2. Review **Troubleshooting** section above
3. Examine the script source code for implementation details
4. Contact the data engineering team

---

**Happy Documenting!** 🚀

# dbt Mapping Documentation Generator

> Automatically reverse-engineers comprehensive mapping documentation for dbt models by analyzing SQL code, schema files, and Snowflake metadata.

**Status:** ✅ Production Ready | **Version:** 1.0.0

---

## 🎯 Overview

This tool generates detailed data lineage and mapping documentation for dbt models (Silver/Gold layers) by:

1. **Parsing dbt SQL code** to extract column transformations and lineage
2. **Reading schema.yml** files for business descriptions
3. **Querying Snowflake** for production metadata
4. **Combining all sources** into a comprehensive mapping document
5. **Exporting to CSV** (importable to Google Sheets)

Perfect for:
- Data governance and compliance
- Onboarding new team members
- Documenting data lineage
- Impact analysis
- Audit trails

---

## 📋 Output Format

Generates mapping documentation with these columns:

| Column | Description | Source |
|--------|-------------|--------|
| **Table Name** | Full model name (layer__domain__table) | dbt |
| **Column Name** | Technical column name | Snowflake |
| **Logical Column Name** | Business-friendly name | Auto-generated |
| **Column Description** | Business description | schema.yml / Snowflake |
| **Table Description** | Table-level description | schema.yml / Snowflake |
| **R3/R3+** | Direct (R3) or Transformed (R3+) | SQL analysis |
| **Value** | Data type | Snowflake |
| **Remarks** | Auto-generated notes | Analysis |
| **Queries** | Manual field | - |
| **Query team** | Manual field | - |
| **Comment** | Transformation logic | SQL parsing |
| **Source Team** | Owning team | Schema mapping |
| **Upstream Table Name** | Source tables | SQL parsing |
| **Upstream Column Name** | Source columns | SQL parsing |
| **Additional Comments** | Tests, validations | schema.yml |

---

## 🚀 Quick Start

### Prerequisites

```bash
pip3 install snowflake-connector-python pyyaml sqlparse
```

### Usage

```bash
python3 scripts/generate_mapping_doc.py \
  --model silver__core__casa \
  --repo /path/to/dbt-repo \
  --sf-account your-account-prod \
  --sf-user your.email@company.com \
  --sf-role TRANSFORMER \
  --sf-warehouse TRANSFORM_WH \
  --output silver_core_casa_mapping.csv
```

### What Happens

```
1. Analyzing dbt SQL code...
   Found: /path/to/models/silver/core/silver__core__casa.sql
   Extracted 45 columns

2. Loading schema documentation...
   Found documentation for 13 columns

3. Querying Snowflake metadata...
   Retrieved metadata for 45 columns

4. Generating mapping documentation...
   ✓ Generated 45 mapping rows

✓ Exported to: silver_core_casa_mapping.csv
  Import this CSV to Google Sheets
```

### Import to Google Sheets

1. Open Google Sheets
2. File → Import
3. Upload → Select the generated CSV
4. Import location: Replace spreadsheet
5. ✓ Done!

---

## 💡 Features

### Intelligent SQL Parsing

Extracts column lineage from complex dbt SQL:
- ✅ CTEs (Common Table Expressions)
- ✅ CASE statements
- ✅ Type casts and conversions
- ✅ Aggregations (SUM, AVG, COUNT, etc.)
- ✅ Window functions
- ✅ Nested subqueries

### Automatic Lineage Tracing

Identifies upstream dependencies:
- `ref()` calls → dbt model references
- `source()` calls → Raw source tables
- Column-level lineage → Which source columns feed each output column

### Smart R3/R3+ Detection

Automatically determines:
- **R3** (Direct): Column passed through without transformation
- **R3+** (Transformed): Column has logic applied (CASE, CAST, calculations)

### Business Context Integration

Combines:
- Technical metadata (Snowflake)
- Business descriptions (schema.yml)
- Transformation logic (SQL code)
- Data quality tests (schema.yml tests)

---

## 📊 Example Output

### Input Model: `silver__core__casa_transactions`

**dbt SQL:**
```sql
with source as (
    select * from {{ ref('bronze__core__casa_transactions') }}
),

transformed as (
    select
        txn_id,
        txn_date,
        account_number,
        case 
            when drcr_ind = 'D' then 'Debit'
            when drcr_ind = 'C' then 'Credit'
            else 'Unknown'
        end as transaction_type,
        txn_amount::decimal(18,2) as transaction_amount
    from source
)

select * from transformed
```

**Generated Mapping:**

| Table Name | Column Name | Logical Name | Column Desc | R3/R3+ | Value | Comment | Upstream Table | Upstream Column |
|------------|-------------|--------------|-------------|--------|-------|---------|----------------|-----------------|
| silver__core__casa_transactions | TXN_ID | Txn Id | Transaction unique identifier | R3 | VARCHAR | txn_id | bronze__core__casa_transactions | TXN_ID |
| silver__core__casa_transactions | TRANSACTION_TYPE | Transaction Type | Type of transaction | R3+ | VARCHAR | CASE WHEN drcr_ind = 'D'... | bronze__core__casa_transactions | DRCR_IND |
| silver__core__casa_transactions | TRANSACTION_AMOUNT | Transaction Amount | Transaction amount in decimal | R3+ | DECIMAL(18,2) | txn_amount::decimal(18,2) | bronze__core__casa_transactions | TXN_AMOUNT |

---

## 🏗️ Architecture

```
┌─────────────────┐
│   dbt Repo      │
│                 │
│ • SQL files     │
│ • schema.yml    │
└────────┬────────┘
         │
         │  Parse SQL & YAML
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ DbtModelAnalyzer│◄─────┤  Snowflake       │
│                 │      │  Metadata        │
│ • Extract CTEs  │      │                  │
│ • Parse columns │      │ • Column types   │
│ • Trace lineage │      │ • Descriptions   │
│ • Find sources  │      │ • Constraints    │
└────────┬────────┘      └─────────┬────────┘
         │                         │
         │                         │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  MappingDocGenerator │
         │                      │
         │  • Combine metadata  │
         │  • Determine R3/R3+  │
         │  • Generate remarks  │
         │  • Trace lineage     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   CSV Export         │
         │   (Google Sheets)    │
         └──────────────────────┘
```

---

## 🔧 Configuration

### Custom Team Mapping

Edit `generate_mapping_doc.py` line ~445:

```python
def _determine_source_team(self, layer: str, schema: str) -> str:
    team_mapping = {
        'core': 'Core Banking Team',
        'payment': 'Payment Team',
        'your_domain': 'Your Team Name'
    }
    return team_mapping.get(schema.lower(), 'Data Platform Team')
```

### Custom R3/R3+ Rules

Edit `generate_mapping_doc.py` line ~430:

```python
def _determine_r3_status(self, transformation: str) -> str:
    # Add your custom logic here
    if 'YOUR_PATTERN' in transformation:
        return 'R3+'
    return 'R3'
```

---

## 📖 Use Cases

### 1. Data Governance

Generate comprehensive data dictionaries for compliance:
```bash
# Generate for all silver models
for model in silver__core__*; do
    python3 scripts/generate_mapping_doc.py \
        --model $model \
        --repo /path/to/repo \
        --sf-account prod \
        --sf-user user@company.com \
        --output docs/${model}_mapping.csv
done
```

### 2. Impact Analysis

Understand downstream impact before changes:
```bash
# Document current state
python3 scripts/generate_mapping_doc.py \
    --model silver__core__customers \
    --repo /path/to/repo \
    --output before_change.csv

# Make changes, then document again
python3 scripts/generate_mapping_doc.py \
    --model silver__core__customers \
    --output after_change.csv

# Compare the two CSVs
```

### 3. Onboarding Documentation

Create instant documentation for new team members:
```bash
# Generate docs for key models
python3 scripts/generate_mapping_doc.py \
    --model silver__core__accounts \
    --output onboarding/accounts_mapping.csv
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **SQL parsing fails** | Check for unsupported SQL syntax; file an issue |
| **Missing columns** | Verify column exists in both dbt SQL and Snowflake |
| **Incorrect lineage** | Complex CTEs may need manual verification |
| **Empty descriptions** | Add descriptions to schema.yml files |
| **Wrong team assignment** | Update team mapping in `_determine_source_team()` |

---

## 📝 Limitations

- SQL parsing is heuristic-based (complex CTEs may not parse perfectly)
- R3/R3+ detection is based on simple patterns
- Manual fields (Queries, Query team) must be filled post-generation
- Macro expansion not supported (shows macro call, not expanded SQL)
- Dynamic SQL not analyzed

---

## 🔮 Future Enhancements

- [ ] Direct Google Sheets API integration (no CSV export needed)
- [ ] Batch processing for multiple models
- [ ] dbt macro expansion
- [ ] Visual lineage diagrams
- [ ] Change detection (compare versions)
- [ ] Automated business glossary lookup
- [ ] Confluence export
- [ ] Custom template support

---

## 📄 License

MIT License

---

## 👥 Authors

**Harikrishnan R** - Data Engineering

---

**Last Updated:** February 27, 2026  
**Version:** 1.0.0

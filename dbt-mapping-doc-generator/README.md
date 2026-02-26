# dbt Mapping Documentation Generator

> Automatically reverse-engineers comprehensive mapping documentation for dbt models by analyzing SQL code, schema files, and Snowflake metadata.

**Status:** ✅ Production Ready | **Version:** 2.0.0 (Enhanced CASE Parsing)

---

## 🆕 Version 2.0 Updates

**Enhanced CASE Statement Parsing:**
- ✅ Captures complex multi-line CASE statements with full logic
- ✅ Handles Jinja templates (`{% if env_var... %}`) within SQL
- ✅ Extracts enum values from CASE WHEN/THEN conditions
- ✅ Improved column lineage extraction (34+ columns vs 11 before)
- ✅ Accurate R3/R3+ classification (direct vs transformed)

**Use `generate_enhanced_mapping.py` for best results** (see below for usage)

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
pip3 install snowflake-connector-python pyyaml
```

### Option 1: Enhanced Version (Recommended) - Uses Pre-extracted Snowflake Data

**Best for:** Complex models with CASE statements, no Snowflake auth needed

```bash
python3 scripts/generate_enhanced_mapping.py \
  silver__core__casa_transactions \
  /path/to/dbt-repo/models/silver/core/silver__core__casa_transactions.sql \
  /path/to/snowflake_inventory.json \
  /path/to/dbt-repo \
  casa_transactions_mapping.csv
```

**Features:**
- ✅ Parses complex multi-line CASE statements
- ✅ Extracts CASE logic with WHEN/THEN conditions
- ✅ Captures enum values from CASE statements
- ✅ Handles Jinja templates in SQL
- ✅ No live Snowflake connection required (uses inventory JSON)
- ✅ 3x more column transformations captured

### Option 2: Original Version - Live Snowflake Connection

**Best for:** Real-time metadata, when you have Snowflake access

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

### What Happens (Enhanced Version)

```
1. Parsing SQL file with enhanced CASE parser...
   ✓ Found 3 upstream tables
   ✓ Found 10 CTEs
   ✓ Parsed 34 column transformations
   ✓ Identified 5 CASE statements

2. Loading schema.yml...
   ✓ Found DQ rules for 13 columns

3. Loading Snowflake metadata...
   ✓ Found 45 columns

4. Generating mapping documentation...

5. Upstream Tables (3):
   - bronze__core_transaction_history__transactions_posting
   - bronze__projections__accounts__account_gl_id_mapping
   - silver__onboarding__customer_master

✓ Generated comprehensive mapping doc
  Total columns: 45
  Upstream tables: 3
  Columns with DQ rules: 12
  Columns with enums: 6
  Transformed columns (R3+): 17
  CASE statements parsed: 5
```

### Import to Google Sheets

1. Open Google Sheets
2. File → Import
3. Upload → Select the generated CSV
4. Import location: Replace spreadsheet
5. ✓ Done!

---

## 💡 Features

### Enhanced SQL Parsing (v2.0)

**Advanced CASE Statement Handling:**
- ✅ Multi-line CASE statements with nested conditions
- ✅ Extracts all WHEN/THEN/ELSE branches
- ✅ Captures enum values from CASE logic
- ✅ Handles Jinja templates (`{% if env_var... %}`)
- ✅ Respects CASE...END block boundaries

**Intelligent Parsing:**
- ✅ CTEs (Common Table Expressions)
- ✅ Complex CASE statements (nested, multi-line)
- ✅ Type casts and conversions
- ✅ Aggregations (SUM, AVG, COUNT, etc.)
- ✅ Window functions
- ✅ Nested subqueries

### Automatic Lineage Tracing

Identifies upstream dependencies:
- `ref()` calls → dbt model references
- `source()` calls → Raw source tables
- Column-level lineage → Which source columns feed each output column
- CTE alias mapping → Traces through intermediate transformations

### Smart R3/R3+ Detection

Automatically determines:
- **R3** (Direct): Column passed through without transformation
- **R3+** (Transformed): Column has logic applied (CASE, CAST, calculations, NULL defaults)

### Business Context Integration

Combines:
- Technical metadata (Snowflake)
- Business descriptions (schema.yml)
- Transformation logic (SQL code with full CASE statements)
- Data quality tests (schema.yml tests)
- Enum values (from both schema.yml and CASE statements)

---

## 📊 Example Output

### Input Model: `silver__core__casa_transactions`

**Complex CASE Statement in SQL:**
```sql
case
    when txn.debit_or_credit = 'credit' then 'CR'
    when txn.debit_or_credit = 'debit' then 'DR'
    else 'NA'
end as drcr_ind
```

**Extracted Mapping:**
```
Column Name: DRCR_IND
R3/R3+: R3+ (Transformed)
Transformation Logic: WHEN txn.debit_or_credit = 'credit' THEN 'CR' 
                     | WHEN txn.debit_or_credit = 'debit' THEN 'DR' 
                     | ELSE 'NA'
Enums: CR, DR, NA
Upstream: bronze__core_transaction_history__transactions_posting -> debit_or_credit
DQ Rules: not_null
```

**Another Example - Multi-line CASE with Nested Conditions:**
```sql
case
    when (
        upper(txn.transaction_domain) = 'DEBIT_CARD'
        or gl_id = '105111'
        or (
            txn.transaction_type in ('REWARD_PAYOUT', 'REWARD_PAYOUT_REVERSAL')
            and txn.transaction_subtype = 'DEBIT_CARD_CASHBACK'
        )
    ) then '120200'
    when txn.product_variant_code = 'BOOST_POCKET'
    {% if env_var("DBT_PROFILE_TARGET") in ["dev", "stg"] %}
        then '310301'
    {% else %}
        then '310101'
    {% endif %}
    when txn.product_variant_code = 'BIZ_DEPOSIT_ACCOUNT'
        then '310200'
    else '310100'
end as gl_product
```

**Extracted Mapping:**
```
Column Name: GL_PRODUCT
R3/R3+: R3+ (Transformed)
Transformation Logic: WHEN (upper(txn.transaction_domain) = 'DEBIT_CARD' ... THEN '120200' 
                     | WHEN txn.product_variant_code = 'BOOST_POCKET' THEN '310301' 
                     | WHEN txn.product_variant_code = 'BIZ_DEPOSIT_ACCOUNT' THEN '310200' 
                     | ELSE '310100'
Enums: 120200, 310301, 310200, 310100
Upstream: bronze__core_transaction_history__transactions_posting -> transaction_domain
DQ Rules: not_null
```
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

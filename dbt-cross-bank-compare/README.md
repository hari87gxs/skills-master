# dbt Cross-Bank Model Comparison Tool

> A comprehensive tool for comparing dbt models across multiple banks/organizations at the column level. Extracts accurate schema information from Snowflake and generates detailed comparison reports in multiple formats.

**Status:** ✅ Production Ready | **Version:** 2.0.0 | **Last Updated:** February 27, 2026

---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Real-World Example](#real-world-example)
- [Output Files](#output-files)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🧠 Overview

This tool automates the complex task of comparing dbt models across multiple banks at the production schema level:

1. **Extracts** complete column information directly from Snowflake `information_schema`
2. **Compares** models at deep column level across banks
3. **Categorizes** models intelligently:
   - **Identical** (100% match) - Ready for immediate homogenization ✅
   - **Similar** (70-99% match) - Low effort to align ⚠️  
   - **Divergent** (<70% match) - Requires business decisions 🔴
   - **Bank-specific** - Exists in only one bank 🔵
4. **Generates** comprehensive reports in multiple formats
5. **Provides** actionable recommendations and phased implementation plan

---

## 🎯 Features

### ✅ Accurate Column Extraction
- Extracts schema directly from Snowflake `information_schema.columns`
- Supports browser-based SSO authentication
- Queries multiple databases (LANDING/Bronze, SILVER, GOLD)
- Captures complete column metadata (names, data types, nullability)
- **100% accurate** - reflects production reality

### 📊 Deep Column-Level Comparison
- Matches models by name across banks
- Calculates similarity percentages based on shared columns
- Identifies column differences (bank-specific columns)
- Compares data types for common columns
- Detects type mismatches

### 🎨 Multiple Report Formats
- **Interactive HTML** - Expandable sections, search, scrollable
- **Google Docs HTML** - Simple tables, easy to share
- **JSON** - Raw data for analysis

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Snowflake Extraction                         │
│              (Browser-based SSO Authentication)                 │
└───────────────┬──────────────────────┬──────────────────────────┘
                │                      │
         ┌──────▼──────┐        ┌──────▼──────┐
         │  Bank A     │        │   Bank B    │
         │  Snowflake  │        │  Snowflake  │
         │             │        │             │
         │ • LANDING   │        │ • LANDING   │
         │ • SILVER    │        │ • SILVER    │
         │ • GOLD      │        │ • GOLD      │
         └──────┬──────┘        └──────┬──────┘
                │                      │
                └──────────┬───────────┘
                           │
                    ┌──────▼──────┐
                    │   Compare   │
                    │   Models    │
                    │  (Column    │
                    │   Level)    │
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
         ┌──────▼─────┐  ┌─▼────┐  ┌─▼──────────┐
         │ Interactive│  │ JSON │  │ Google Docs│
         │    HTML    │  │ Data │  │    HTML    │
         └────────────┘  └──────┘  └────────────┘
```

---

## 📦 Installation

### Prerequisites
- Python 3.7+
- Snowflake account access for both banks
- Browser-based SSO authentication enabled

### Install Dependencies
```bash
pip3 install snowflake-connector-python
```

---

## 🚀 Usage

### Step 1: Extract Schema from Snowflake

Extract complete column information from each bank's Snowflake:

```bash
# Bank A (e.g., GXS Bank)
python3 scripts/extract_from_snowflake.py \
  --account gxs-prod \
  --user your.email@bankA.com \
  --role TRANSFORMER \
  --warehouse TRANSFORM_WH \
  --repo-name "Bank A" \
  --output bankA_inventory.json

# Bank B (e.g., GXBank)
python3 scripts/extract_from_snowflake.py \
  --account abc123.southeast-asia.azure \
  --user your.email@bankB.com \
  --role TRANSFORMER \
  --warehouse TRANSFORM_WH \
  --repo-name "Bank B" \
  --output bankB_inventory.json
```

**What happens:**
- Browser window opens for SSO authentication
- Queries `information_schema.columns` for all databases
- Extracts complete column metadata
- Saves to JSON file

**Example output:**
```
Connecting to Snowflake account: gxs-prod
⚠️  A browser window will open for authentication...
✓ Successfully connected to Snowflake!

Querying LANDING database...
  Found 853 tables with 17,343 columns
Querying SILVER database...
  Found 889 tables with 20,115 columns  
Querying GOLD database...
  Found 6,316 tables with 273,528 columns

Statistics:
  Total tables: 8,058
  Total columns: 310,986

✓ Saved inventory to bankA_inventory.json
✓ Verification: silver__core__casa_transactions has 45 columns
```

### Step 2: Compare Models

Run deep column-level comparison:

```bash
python3 scripts/compare_snowflake_models.py
```

**Note:** Edit the script to point to your inventory files.

**Example output:**
```
================================================================================
DEEP MODEL COMPARISON - Column Level Analysis
================================================================================

Model overlap:
  Common models (same name): 468
  Bank A-only models: 7,590
  Bank B-only models: 4,183

Common Models Analysis:
  Identical (100% match): 195 models
  Similar (70-99% match): 190 models
  Divergent (<70% match): 83 models

✓ Saved comparison results to comparison_results.json
```

### Step 3: Generate Reports

#### Interactive HTML Report
```bash
python3 scripts/generate_html_snowflake.py comparison_results.json
```

Output: `~/.agent/reports/dbt-cross-bank-comparison-snowflake.html`

Features:
- Expandable/collapsible sections
- Search within sections
- Scrollable content
- Detailed column differences
- Sorted by column count

#### Google Docs Compatible Report
```bash
python3 scripts/generate_gdocs_html.py comparison_results.json
```

Output: `~/.agent/reports/dbt-comparison-gdocs.html`

**To import to Google Docs:**
1. Go to [docs.google.com](https://docs.google.com)
2. File → Open → Upload
3. Select the generated HTML file
4. Google Docs will automatically convert it

---

## 💼 Real-World Example

### Context
- **Banks**: GXS Bank (Singapore) & GXBank (Malaysia)
- **Goal**: Identify models that can be homogenized across banks
- **Data Source**: Production Snowflake
  - GXS: 8,058 models, 310,986 columns
  - GXBank: 4,651 models, 179,895 columns

### Results

#### Common Models (468 total)
| Category | Count | % | Action |
|----------|-------|---|--------|
| **Identical** | 195 | 41.7% | ✅ Ready for immediate homogenization |
| **Similar** | 190 | 40.6% | ⚠️ Low effort - minor adjustments |
| **Divergent** | 83 | 17.7% | ❌ Requires business decisions |

#### Bank-Specific Models
| Bank | Total | Gold | Silver | Bronze |
|------|-------|------|--------|--------|
| **GXS-only** | 7,590 | 6,142 | 843 | 605 |
| **GXBank-only** | 4,183 | 3,119 | 546 | 518 |

#### Example: `silver__core__casa_transactions`
```
Model: silver__core__casa_transactions
├─ Layer: Silver (core business logic)
├─ GXS Columns: 45
├─ GXBank Columns: 81
├─ Common Columns: 34 (overlap)
├─ Similarity: 36.96% (Divergent)
├─ GXS-only: 11 columns
│  └─ TXN_CARD_NOT_PRESENTED_FLAG, ON_US_OFF_US_IND, ...
└─ GXBank-only: 47 columns
   └─ Additional transaction attributes
```

**Analysis:** Significant differences require business review to determine:
- Which columns are truly needed?
- Can approaches be merged?
- Should this remain bank-specific?

---

## 📂 Output Files

### 1. Inventory Files (JSON)
Complete schema information per bank:

```json
{
  "repo_name": "Bank A",
  "account": "gxs-prod",
  "models": {
    "silver__core__casa_transactions": {
      "name": "silver__core__casa_transactions",
      "layer": "silver",
      "domain": "core",
      "table": "casa_transactions",
      "columns": [
        {
          "name": "TXN_ID",
          "position": 1,
          "data_type": "VARCHAR",
          "nullable": false,
          "database": "SILVER",
          "schema": "CORE"
        }
      ],
      "column_count": 45,
      "database": "SILVER",
      "schema": "CORE"
    }
  },
  "statistics": {
    "total_models": 8058,
    "total_columns": 310986,
    "by_layer": {
      "gold": 6316,
      "silver": 889,
      "landing": 853
    }
  }
}
```

### 2. Comparison Results (JSON)
Detailed model-by-model comparison:

```json
{
  "identical": [...],
  "similar": [...],
  "divergent": [
    {
      "name": "silver__core__casa_transactions",
      "layer": "silver",
      "domain": "core",
      "table": "casa_transactions",
      "comparison": {
        "similarity_pct": 36.96,
        "gxs_col_count": 45,
        "gxbank_col_count": 81,
        "common_col_count": 34,
        "gxs_only_col_count": 11,
        "gxbank_only_col_count": 47,
        "common_cols": ["TXN_ID", "TXN_DATE", ...],
        "gxs_only_cols": ["TXN_CARD_NOT_PRESENTED_FLAG", ...],
        "gxbank_only_cols": ["ADDITIONAL_ATTR", ...],
        "type_matches": 34,
        "type_mismatches": []
      }
    }
  ],
  "gxs_only": {
    "silver": [...]
  },
  "gxbank_only": {
    "silver": [...]
  },
  "summary": {
    "identical_count": 195,
    "similar_count": 190,
    "divergent_count": 83,
    "gxs_only_count": 7590,
    "gxbank_only_count": 4183,
    "common_models_count": 468
  }
}
```

### 3. Interactive HTML Report
- Expandable sections for each category
- Searchable model lists
- Detailed column-level comparisons
- Visual similarity indicators
- Scrollable content areas

### 4. Google Docs HTML Report
- Simple table format
- Easy to import and edit
- Shareable with stakeholders
- Includes recommendations

---

## ⚙️ Configuration

### Snowflake Connection

Edit `scripts/extract_from_snowflake.py`:

```python
# Connection parameters
account = "your-account.region.cloud"
user = "your.email@company.com"
role = "TRANSFORMER"
warehouse = "TRANSFORM_WH"
authenticator = "externalbrowser"  # Browser-based SSO

# Databases to query
databases = ["LANDING", "SILVER", "GOLD"]
```

### Similarity Thresholds

Edit `scripts/compare_snowflake_models.py`:

```python
# Categorization thresholds
IDENTICAL_THRESHOLD = 100.0    # 100% match
SIMILAR_THRESHOLD = 70.0       # 70-99% match
# Below 70% = Divergent
```

---

## 💡 Best Practices

### Data Extraction
1. ✅ Use production Snowflake for accurate schema
2. ✅ Run extractions regularly to track schema changes
3. ✅ Store inventory files in version control
4. ✅ Document extraction date in filenames

### Comparison Analysis
1. ✅ Prioritize Silver layer (business logic)
2. ✅ Focus on high-usage models (transactions, accounts)
3. ✅ Review divergent models with business stakeholders
4. ✅ Track alignment progress over time

### Phased Implementation

**Phase 1: Quick Wins (Identical)**
- Target: 195 identical models
- Priority: Silver layer
- Effort: Low (configuration)
- Timeline: 1-2 sprints

**Phase 2: Low-Effort Alignment (Similar)**
- Target: 190 similar models
- Actions: Add/remove columns
- Effort: Medium (code changes)
- Timeline: 2-3 months

**Phase 3: Strategic (Divergent)**
- Target: 83 divergent models
- Actions: Business review
- Effort: High
- Timeline: 3-6 months

**Phase 4: Bank-Specific Evaluation**
- Target: 11,773 models
- Actions: Determine market-specific vs standardization candidates
- Effort: Ongoing
- Timeline: 6-12 months

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser authentication fails | Ensure Snowflake permissions and SSO enabled |
| Query timeout | Increase timeout or query databases separately |
| Missing columns | Verify database/schema structure matches |
| Google Docs import fails | Open in browser first, then copy-paste |
| Incorrect column counts | Ensure querying production, not dev schemas |

---

## 📝 Limitations

- Schema comparison only (not SQL transformation logic)
- Column names compared case-insensitively
- Data type comparison is exact match
- Does not include column comments in similarity
- Large schemas (10,000+ tables) may take time

---

## 🚧 Future Enhancements

- [ ] SQL transformation logic comparison
- [ ] Column lineage analysis
- [ ] Multi-cloud support (AWS, Azure, GCP)
- [ ] Automated alignment recommendations
- [ ] Target state schema generator
- [ ] Data type compatibility matrix
- [ ] Column rename detection
- [ ] Historical tracking
- [ ] CI/CD integration

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Authors

**Harikrishnan R** - Data Engineering

---

## 🙏 Acknowledgments

- Built with Python and Snowflake Connector
- Inspired by dbt best practices
- Developed for cross-bank data platform homogenization

---

**Last Updated:** February 27, 2026  
**Version:** 2.0.0  
**Status:** ✅ Production Ready

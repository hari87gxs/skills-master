# dbt Cross-Bank Model Comparison & Homogenization Skill

> An **OpenCode Skill** that performs deep column-level comparison of two dbt transformer repositories across banks (GXS vs GXBank), identifies truly common, divergent, and unique models, and generates a comprehensive dual-strategy homogenization plan with interactive HTML reports and progress tracking.

---

## 🧠 What Does This Skill Do?

This skill automates the complex task of comparing and aligning data transformation code across multiple banks. It:

1. **Clones** two dbt transformer repos (e.g., GXS Bank & GXBank)
2. **Extracts** detailed model inventories with column-level metadata
3. **Compares** models using intelligent categorization:
   - **Identical**: Same name + same columns + same logic ✅
   - **Similar**: Same columns, minor logic differences ⚠️
   - **Divergent**: Different columns or major logic differences 🔴
   - **Unique**: Only in one bank 🔵/🟣
4. **Generates** an interactive HTML report with:
   - Comparison matrix (sortable/filterable)
   - Side-by-side column diffs
   - SQL logic analysis
   - Dependency impact maps
   - Dual homogenization strategies (shared package + manual convergence)
5. **Tracks progress** over time (supports re-runs)

---

## 🎯 Key Features

### Deep Column-Level Analysis

Unlike simple file comparison, this skill:
- Parses SQL SELECT clauses to extract column names
- Captures column transformation logic (e.g., `CASE WHEN`, `SUM()`, type casts)
- Compares logic line-by-line to detect subtle differences
- Identifies column renames, missing columns, and type mismatches

### Smart Categorization

**"Common" models must match on THREE criteria:**
1. ✅ Domain + table name
2. ✅ Column names (all columns present in both)
3. ✅ Column logic (transformations must be equivalent)

This prevents false positives where models share names but have different implementations.

### Priority-Based Analysis

Analyzes layers in business-priority order:
1. **Silver** (highest priority - conformed layer)
2. **Gold** (reporting layer)
3. **Bronze** (raw data layer)

### Dual Homogenization Strategies

Recommends **both** approaches with pros/cons:
- **Strategy 1**: Shared dbt package (`gx-shared-models`) for long-term consistency
- **Strategy 2**: Manual convergence roadmap for quick wins

---

## 📂 Files

```
dbt-cross-bank-compare/
├── SKILL.md          ← OpenCode skill definition (this is the brain)
└── README.md         ← This file (documentation)
```

---

## ⚙️ Installation

### 1. Copy skill to OpenCode

```bash
cp -r dbt-cross-bank-compare ~/.config/opencode/skills/
```

### 2. Restart OpenCode or reload skills

The skill will be automatically available.

---

## 💬 Usage

### Basic Usage

In OpenCode chat:

```
Compare the GXS and GXBank transformer repos:
- GXS: https://gitlab.com/gx-regional/dakota/data-platform/digibank-transformer
- GXBank: https://gitlab.com/gx-regional/dbmy/data-platform/dbmy-transformer
PAT: glpat-xxxxxxxxxxxxx
```

### The skill will prompt you for:
- GXS Bank repo URL
- GXBank repo URL
- GitLab Personal Access Token (same for both)
- Report name (optional)

### What Happens Next:

1. **Clones both repos** to `/tmp/compare-gxs` and `/tmp/compare-gxbank`
2. **Extracts model inventories** using Python script:
   - Reads all `.sql` files in `models/silver`, `models/gold`, `models/bronze`
   - Parses SELECT clauses to extract columns and logic
   - Extracts `ref()` dependencies
3. **Performs deep comparison**:
   - Groups models by full name (layer.domain.model)
   - Compares column names and logic
   - Categorizes as identical/similar/divergent/unique
4. **Generates HTML report** at:
   ```
   ~/.agent/reports/dbt-cross-bank-comparison-<timestamp>.html
   ```
5. **Opens report in browser**
6. **Shows summary in chat**:
   ```
   ✅ Comparison complete!
   
   📊 Summary:
   - Identical models: 42 (can reuse immediately)
   - Similar models: 18 (minor alignment needed)
   - Divergent models: 23 (significant work required)
   - GXS-only: 15
   - GXBank-only: 8
   
   🎯 Top recommendations:
   1. Extract 42 identical silver models to shared package
   2. Prioritize converging top 5 divergent silver models
   3. Evaluate 8 country-specific models for regional differences
   
   📄 Full report: ~/.agent/reports/dbt-cross-bank-comparison-2026-02-27.html
   ```
7. **Cleans up** temporary repos

---

## 📊 Output Report Structure

### 1. Executive Summary
- Model counts by layer and status
- Pie chart: Identical/Similar/Divergent/Unique split
- Key findings and recommendations

### 2. Interactive Comparison Matrix

| Priority | Layer | Domain | Model | GXS | GXBank | Status | Column Match | Logic Match | Action |
|----------|-------|--------|-------|-----|--------|--------|--------------|-------------|--------|
| 1 | silver | core | accounts | ✓ | ✓ | Divergent | 80% | No | Merge |
| 1 | silver | core | transactions | ✓ | ✓ | Similar | 100% | 95% | Align |
| 1 | silver | lending | loan_core | ✓ | ✓ | Identical | 100% | 100% | Reuse |

**Features:**
- Sortable by any column
- Filterable by layer/status/domain
- Click to expand details

### 3. Identical Models
List of models ready for immediate reuse in shared package

### 4. Divergent Models Deep Dive

For each divergent model:

**Column comparison table:**
```
Model: silver.core.accounts

| Column | GXS Logic | GXBank Logic | Match |
|--------|-----------|--------------|-------|
| account_id | core_accounts.id | core_accounts.account_number | ✗ Different source |
| balance | amount::decimal(18,2) | amount | ✗ Type mismatch |
| status | CASE WHEN active THEN 'ACTIVE' ... | status_code | ✗ Logic different |
```

**Logic differences (high-level):**
- ✓ Same WHERE clause
- ✗ Different JOIN logic (GXS: 3 joins, GXBank: 2 joins)
- ✗ Different aggregations (GXS: SUM, GXBank: MAX)

**Dependency graph:**
Mermaid diagram showing different upstream sources

**Recommended action:**
```
Action: Merge logic
1. Use GXS as base
2. Add GXBank column: account_type
3. Standardize column names
4. Test with both downstream dependencies
Effort: 2 days | Priority: High
```

### 5. Unique Models Analysis
- GXS-only models (assess if GXBank needs)
- GXBank-only models (assess if GXS needs)
- Country-specific flags

### 6. Dual Homogenization Strategies

**Strategy 1: Shared dbt Package**
```
Approach: Extract to gx-shared-models package
Pros: Single source of truth, enforced consistency
Cons: Initial overhead, dependency management
Effort: 3-4 sprints
```

**Strategy 2: Manual Convergence**
```
Approach: Layer-by-layer, domain-by-domain convergence
Pros: Faster start, no new infrastructure
Cons: Ongoing maintenance, risk of re-divergence
Effort: 6-8 sprints
```

### 7. Dependency Impact Map
Mermaid graph showing cascade effects of changes

### 8. Progress Tracker (for re-runs)
- % identical models over time
- Newly converged models since last run
- Convergence trend chart

---

## 🔍 How It Works: Column-Level Comparison

### Example: Detecting Divergence

**GXS model (silver.core.accounts):**
```sql
SELECT
    account_id,
    customer_id,
    UPPER(account_type) AS account_type,
    amount::decimal(18,2) AS balance,
    CASE 
        WHEN active = TRUE THEN 'ACTIVE'
        ELSE 'INACTIVE'
    END AS status
FROM {{ ref('bronze', 'core_accounts_service') }}
```

**GXBank model (silver.core.accounts):**
```sql
SELECT
    account_number AS account_id,
    cust_id AS customer_id,
    acc_type AS account_type,
    amount AS balance,
    status_code AS status
FROM {{ ref('bronze', 'core_banking_system') }}
```

**Skill's Analysis:**

| Column | GXS Logic | GXBank Logic | Status |
|--------|-----------|--------------|--------|
| account_id | account_id | account_number AS account_id | ✗ Different source column |
| customer_id | customer_id | cust_id AS customer_id | ✗ Different source column |
| account_type | UPPER(account_type) AS account_type | acc_type AS account_type | ✗ Logic different (UPPER missing) |
| balance | amount::decimal(18,2) AS balance | amount AS balance | ✗ Type cast different |
| status | CASE WHEN active = TRUE... | status_code AS status | ✗ Logic different (CASE missing) |

**Recommendation:**
```
Status: Divergent
Action: Standardize logic
1. Align source column names
2. Add UPPER() transformation to GXBank
3. Add type cast to GXBank: amount::decimal(18,2)
4. Standardize status logic using CASE statement
Effort: 1 day
Priority: High (silver layer, core domain)
```

---

## 🛠️ Technical Details

### Python Column Extraction

The skill uses regex-based SQL parsing to extract columns:

```python
def extract_columns_from_sql(sql_content):
    """
    Extract column names and their logic from SELECT clause.
    Handles:
    - Simple columns: column_name
    - Aliased columns: expression AS column_name
    - Qualified columns: table.column_name AS alias
    """
    # Find SELECT clause (between SELECT and FROM)
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_content, re.IGNORECASE | re.DOTALL)
    
    # Split by comma and parse each column
    # Extract AS aliases and normalize logic
    # Return: {column_name: transformation_logic}
```

### Comparison Algorithm

```python
def compare_columns(gxs_cols, gxbank_cols):
    # Check if column names match
    if gxs_names != gxbank_names:
        return 'divergent'
    
    # Check logic for each column
    for col_name in gxs_names:
        if gxs_cols[col_name] != gxbank_cols[col_name]:
            logic_diffs.append(...)
    
    # Categorize based on number of differences
    if no_diffs: return 'identical'
    elif minor_diffs: return 'similar'
    else: return 'divergent'
```

---

## 📈 Use Cases

### 1. Initial Convergence Assessment
**Scenario**: You've just taken over both banks and want to understand overlap.

**Usage**:
```
Compare GXS and GXBank transformers and show me where we can consolidate
```

**Output**: HTML report showing 42 identical models ready for shared package extraction.

### 2. Ongoing Convergence Tracking
**Scenario**: Your teams are actively converging models. You want to track progress.

**Usage**:
```
Re-run the dbt comparison (weekly)
```

**Output**: Progress tracker showing convergence trend:
- Week 1: 42 identical models
- Week 2: 48 identical models (+6 converged)
- Week 3: 55 identical models (+7 converged)

### 3. Homogenization Planning
**Scenario**: Leadership wants a roadmap for code consolidation.

**Usage**:
```
Generate homogenization plan for GXS and GXBank
```

**Output**: Markdown summary with:
- Executive summary
- Dual strategy recommendations
- Prioritized model list
- Effort estimates

---

## 🔐 Authentication

### GitLab Personal Access Token (PAT)

You need a PAT with `read_repository` scope for both repos:

1. Go to **GitLab → Settings → Access Tokens**
2. Create token with:
   - **Name**: `opencode-dbt-compare`
   - **Scopes**: `read_repository`
3. Copy the token (starts with `glpat-`)
4. Provide it when prompted

**Security**: The skill clones to `/tmp/` and deletes repos after analysis. PAT is never stored.

---

## 🎨 Report Aesthetic

- **Blueprint theme**: Deep navy background, cyan accents
- **Fonts**: IBM Plex Mono + IBM Plex Sans
- **Interactive**: Sortable tables, expandable diffs, filterable views
- **Color coding**:
  - 🟢 Green = Identical
  - 🟡 Yellow = Similar
  - 🔴 Red = Divergent
  - 🔵 Blue = GXS-only
  - 🟣 Purple = GXBank-only

---

## 🐛 Troubleshooting

### Issue: "No models found"

**Cause**: Repo doesn't have expected structure.

**Fix**: Verify repos have `models/silver/`, `models/gold/`, `models/bronze/` directories.

### Issue: "SQL parsing failed"

**Cause**: Complex SQL with nested CTEs or non-standard syntax.

**Fix**: Skill logs warnings but continues. Check report for "unable to parse" models.

### Issue: "Clone failed"

**Cause**: Invalid PAT or network issue.

**Fix**: Verify PAT has `read_repository` scope and check GitLab connectivity.

### Issue: "Out of memory"

**Cause**: Very large repos (>10,000 models).

**Fix**: Skill can be modified to process in batches. Contact maintainer for guidance.

---

## 📝 Output Files

After running the skill:

```bash
~/.agent/reports/
├── dbt-cross-bank-comparison-2026-02-27-143022.html    # Main report
├── comparison-data-2026-02-27-143022.json              # Raw data (optional)
└── homogenization-plan-2026-02-27-143022.md            # Markdown summary (optional)
```

**Sharing reports:**
- HTML files are self-contained (can email or upload to Confluence)
- JSON can be imported to Tableau/PowerBI for executive dashboards
- Markdown can be copy-pasted to Jira tickets

---

## 🚀 Roadmap

Planned enhancements:

- [ ] Support for Snowflake query history comparison (detect runtime divergence)
- [ ] Macro comparison (compare reusable SQL macros across repos)
- [ ] Test coverage comparison (which models have dbt tests)
- [ ] Data quality metrics (row counts, freshness, test pass rates)
- [ ] Slack integration (post weekly convergence summary)
- [ ] GitHub support (in addition to GitLab)

---

## 🤝 Contributing

To improve this skill:

1. Fork the repo
2. Modify `SKILL.md`
3. Test with your dbt projects
4. Submit PR with examples

---

## 📄 License

MIT License — use freely for your projects.

---

## 🙏 Credits

Built with:
- **OpenCode** — AI-powered coding assistant
- **Python** — SQL parsing and analysis
- **Mermaid.js** — Dependency graphs
- **IBM Plex** — Typography

Inspired by the challenges of managing multi-bank data platforms at GXS Bank & GXBank.

# Business Rule Extraction and Python Implementation Runbook

## 1. Purpose and Scope

This runbook describes the end-to-end process used in this repository to:

- **Extract business rules** from SQL stored procedures and database metadata.
- **Create a Python module** that implements those rules using pandas.
- **Generate tests** to validate the business-rule implementation.
- **Automatically iterate / fix issues** by running tests and adjusting code.
- **Execute the logic on sample data** to verify behavior.
- **Commit and push changes to GitHub** after a successful run.

The existing `BLE-SOURCE/sales_summary_rules.*` files are a concrete example of this process for the stored procedure `dbo.usp_CalculateSalesSummary`.

---

## 2. Prerequisites

- **Tools**
  - Python 3.10+ installed.
  - `pip` available.
  - Git installed and configured with your GitHub credentials.

- **Python dependencies (example)**
  - `pandas`
  - `pytest`
  - `openpyxl` (for reading Excel schema metadata)

  Install (from repo root):

  ```bash
  pip install -r requirements.txt  # if present
  ```

  or, explicitly:

  ```bash
  pip install pandas pytest openpyxl
  ```

- **Repository cloned and on a feature branch**
  - Clone from GitHub.
  - Create a working branch, for example:

    ```bash
    git checkout -b feature/new-business-rule
    ```

---

## 3. Source Assets (Inputs)

For each business rule extraction exercise, identify the following inputs.

- **1) SQL definitions & procedures**
  - Example: `BLE-SOURCE/AdevnetureWorks.sql`
  - Contains:
    - Table definitions (fact and dimension tables).
    - Stored procedures (e.g., `dbo.usp_CalculateSalesSummary`).

- **2) Schema metadata**
  - Example: `BLE-SOURCE/schema_metadata.xlsx`
  - Expected columns include at least:
    - `TABLE_SCHEMA`
    - `TABLE_NAME`
    - `COLUMN_NAME`
  - Used to validate required tables/columns before running business rules.

- **3) Sample or synthetic data**
  - Example artifacts already in this repo:
    - `BLE-SOURCE/sampled_data.xlsx`
    - `BLE-SOURCE/synthetic_sales_data.py`
    - `BLE-SOURCE/synthetic_seasonal_*.csv`
  - These provide representative data to execute and test the Python rules.

---

## 4. High-Level Workflow Summary

1. **Identify the target stored procedure** in the SQL file.
2. **Extract and document business rules** (filtering, joins, grouping, calculations, ordering).
3. **Design a Python module** that implements those rules with pandas.
4. **Use schema metadata** to validate that all required tables/columns exist.
5. **Create pytest-based tests** for the Python module.
6. **Run tests and fix issues** until all tests pass.
7. **Execute the Python business rule** using sample/synthetic data.
8. **Review outputs** for correctness and consistency with the SQL procedure.
9. **Commit and push** all artifacts (SQL, Python, tests, docs) to GitHub.

The sections below provide detailed steps.

---

## 5. Extract and Document Business Rules from SQL

1. **Locate the procedure**
   - Open the main SQL file (e.g., `BLE-SOURCE/AdevnetureWorks.sql`).
   - Search for the procedure by name, for example:

     ```sql
     CREATE PROCEDURE [dbo].[usp_CalculateSalesSummary]
     ```

2. **Identify core logical elements** in the procedure:
   - **Inputs**: parameters such as `@StartDate`, `@EndDate`.
   - **Source tables**: e.g., `FactInternetSales`, `DimProduct`, etc.
   - **Filters**: `WHERE` clause (e.g., date range filters).
   - **Joins**: `INNER JOIN` / `LEFT JOIN` chains and join conditions.
   - **Grouping**: `GROUP BY` columns (defines the output grain).
   - **Aggregations**: `SUM`, `COUNT`, `AVG`, etc.
   - **Ordering**: `ORDER BY` rules.

3. **Write the business rules in plain language**
   - Create or update a markdown file in `BLE-SOURCE`, named after the procedure, e.g.:
     - `BLE-SOURCE/sales_summary_rules.md`
   - Document rules as numbered items (BR1, BR2, …). Example patterns:
     - **BR1: Date-Range Filter (Inclusive)** – Only rows where `OrderDate` is between `@StartDate` and `@EndDate` (inclusive).
     - **BR2: Dimension Conformance** – Only rows that successfully join through the dimension keys are included.
     - **BR3: Output Grain** – Grouped by `ProductCategory`.
     - **BR4: Aggregated Metrics** – `TotalSales`, `TotalOrders`, `AverageOrderValue`.
     - **BR5: Business Ordering Rule** – Sort by `TotalSales` descending.

4. **Confirm rule coverage**
   - Ensure that every significant aspect of the SQL logic is represented as an explicit business rule.
   - If something is ambiguous, add assumptions to the markdown document.

---

## 6. Design the Python Business Rule Module

For each procedure, create a dedicated Python module in `BLE-SOURCE` that implements the documented rules.

1. **File naming**
   - Follow the pattern:
     - `<logical_name>_rules.py`
   - Example already present: `BLE-SOURCE/sales_summary_rules.py`.

2. **Module structure (typical)**
   - Imports (e.g., `pandas as pd`).
   - Optional constants describing required columns.
   - **Schema metadata helper(s)**
     - e.g., `load_schema_metadata(path: str) -> pd.DataFrame`.
   - **Schema validation function** specific to this rule set.
   - **Core business-rule function** that reproduces the procedure’s logic using pandas.

3. **Schema validation using metadata**
   - Define a constant list of required `(schema, table, column)` tuples.
   - Implement a function (similar to `validate_schema_for_sales_summary`) that:
     - Verifies the presence of `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME` columns in the metadata.
     - Checks that all required triples are present.
     - Raises a clear `ValueError` if any are missing.

4. **Implement the business-rule function**
   - Inputs typically include:
     - DataFrames for each table used in the procedure (e.g. fact/dimension tables).
     - Parameters corresponding to SQL parameters (e.g. start/end dates).
   - Steps (mapping to the rules):
     - **Coerce data types** (e.g. convert `OrderDate` to datetime).
     - **Apply filters** (e.g. inclusive date range).
     - **Join tables** using pandas `merge`, mirroring SQL joins.
     - **Group and aggregate** to compute metrics.
     - **Rename/format columns** to match the business expectations.
     - **Sort results** based on business ordering rules.
     - **Handle empty result sets** by returning an empty DataFrame with expected columns.

---

## 7. Create Tests for the Business Rules

Use `pytest` to create tests in `BLE-SOURCE` that validate both schema checks and business-rule outputs.

1. **File naming**
   - Follow the pattern:
     - `test_<logical_name>_rules.py`
   - Example already present: `BLE-SOURCE/test_sales_summary_rules.py`.

2. **Test types**

   - **Schema validation tests**
     - Positive case: load the real schema metadata (e.g. `schema_metadata.xlsx`) and assert that validation passes.
     - Negative cases: construct small DataFrames missing either required metadata columns or specific required columns, and assert that validation raises `ValueError`.

   - **Core business-rule tests**
     - Build minimal DataFrames for the relevant tables that:
       - Include a range of dates to test the filter.
       - Have valid and invalid join keys to test join behavior.
     - Call the rule function (e.g. `calculate_sales_summary`).
     - Assert on:
       - The set of group keys (e.g. product categories).
       - Aggregated values (sums, counts, averages).
       - Output ordering.

   - **Parametrized tests (optional)**
     - Use `@pytest.mark.parametrize` to cover multiple negative/edge cases with compact code.

3. **Location of test data**
   - Inline small DataFrames directly in the tests for clarity.
   - For larger or more realistic tests, use the synthetic-data helpers (e.g. from `synthetic_sales_data.py`) or CSV/Excel files in `BLE-SOURCE`.

---

## 8. Run Tests and Automatically Fix Issues

1. **Run the test suite (from repo root)**

   ```bash
   python -m pytest BLE-SOURCE -q
   ```

   or to run only tests for one rule set:

   ```bash
   python -m pytest BLE-SOURCE/test_<logical_name>_rules.py -q
   ```

2. **Interpret failures**
   - If tests fail, use the error messages and stack traces to identify:
     - Schema mismatches.
     - Incorrect joins or filters.
     - Incorrect aggregates or output formats.

3. **Fix code and/or tests**
   - Adjust the Python rule module and tests to align with the documented business rules.
   - Re-run `pytest` until all tests pass.

4. **Optional auto-fix tooling**
   - To automatically handle style/formatting and some simple issues, you may integrate tools like:
     - `black` (code formatting)
     - `ruff` or `flake8` (linting)
   - Typical usage (from repo root):

     ```bash
     black BLE-SOURCE
     ruff check BLE-SOURCE --fix
     ```

   - These tools do **not** replace business-rule thinking, but they automatically fix many syntactic and stylistic issues that cause test or CI failures.

The expectation in this workflow is that you (or an automated assistant) will iteratively run tests and apply fixes until everything passes.

---

## 9. Execute the Logic with Sample Data

After tests are passing, run the business-rule function(s) on realistic sample or synthetic data.

1. **Use synthetic data helpers (example)**
   - For the `sales_summary` example, `BLE-SOURCE/synthetic_sales_data.py` provides:
     - Dimension tables: `create_synthetic_dimensions()`.
     - Fact tables: `create_synthetic_fact_internet_sales()` or the seasonal variant.

2. **Typical execution pattern (conceptual)**
   - In a short driver script or an interactive session:
     - Import the synthetic-data functions and the business-rule function.
     - Construct the DataFrames.
     - Call the business-rule function with an appropriate date range.
     - Inspect the resulting DataFrame (print, export to CSV, etc.).

3. **Compare with expectations**
   - Validate that the outputs align with the documented business rules and any known reference results from SQL.
   - If discrepancies are found, update either:
     - The Python module (if it is wrong), or
     - The documented assumptions (if the SQL semantics are different than expected).

---

## 10. Commit and Push to GitHub

Once the business rules, Python implementation, tests, and documentation are complete and verified:

1. **Review changes**

   ```bash
   git status
   git diff
   ```

2. **Stage relevant files**
   - Include:
     - New/updated markdown rule files in `BLE-SOURCE`.
     - New/updated Python rule modules.
     - New/updated tests.
     - Any supporting data files (if added or changed).

   ```bash
   git add BLE-SOURCE/*.py BLE-SOURCE/*.md BLE-SOURCE/*.csv BLE-SOURCE/*.xlsx
   ```

   (Adjust the patterns to include only the files you actually changed.)

3. **Commit with a meaningful message**

   ```bash
   git commit -m "Implement <procedure_name> business rules in Python with tests"
   ```

4. **Push to GitHub**

   ```bash
   git push origin <your-branch-name>
   ```

5. **Open a Pull Request (PR)**
   - On GitHub, open a PR from your branch to the main branch.
   - In the PR description, reference:
     - The stored procedure(s) implemented.
     - The new Python modules and tests.
     - Any assumptions or limitations.

---

## 11. Reusing This Runbook for New Procedures

When implementing business rules for a new stored procedure:

1. **Copy this process** and adapt names and details.
2. **Create new `*_rules.md` and `*_rules.py` files** in `BLE-SOURCE` following the patterns in the existing example.
3. **Add targeted tests** under `BLE-SOURCE/test_*.py` mirroring the structure of `test_sales_summary_rules.py`.
4. **Run tests, fix issues, execute with sample data, and push to GitHub** as described above.

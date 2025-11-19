# Sales Summary Business Rules and Python Implementation

## Overview

This document describes the business rules implemented by the SQL stored procedure `dbo.usp_CalculateSalesSummary` in `AdevnetureWorks.sql` and how those rules are replicated in Python using `sales_summary_rules.py` with accompanying tests in `test_sales_summary_rules.py`.

The goal is to:

- Extract business rules from the AdventureWorksDW data warehouse objects.
- Validate that the database schema matches the expectations of these rules.
- Provide a Python implementation of the rules for offline analytics or automated checks.
- Supply simple tests that verify the implementation.

## Source Assets

- **SQL DDL & procedure**: `BLE-SOURCE/AdevnetureWorks.sql`
  - Contains the AdventureWorksDW schema and the stored procedure `dbo.usp_CalculateSalesSummary`.
- **Schema metadata**: `BLE-SOURCE/schema_metadata.xlsx`
  - Excel sheet with columns such as `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`, etc.
  - Used to validate that required tables/columns exist.
- **Sample data snapshot**: `BLE-SOURCE/sampled_data.xlsx`
  - Snapshot of `DatabaseLog` entries (DDL events). Useful for auditing but not used directly as fact/dimension input data for the sales summary.
- **Python business-rule module**: `BLE-SOURCE/sales_summary_rules.py`
- **Python tests**: `BLE-SOURCE/test_sales_summary_rules.py`

## Business Rules from `usp_CalculateSalesSummary`

The T-SQL procedure:

```sql
CREATE PROCEDURE [dbo].[usp_CalculateSalesSummary]
    @StartDate DATE,
    @EndDate DATE
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        pc.EnglishProductCategoryName AS ProductCategory,
        SUM(fis.SalesAmount) AS TotalSales,
        COUNT(fis.SalesOrderNumber) AS TotalOrders,
        AVG(fis.SalesAmount) AS AverageOrderValue
    FROM FactInternetSales fis
    INNER JOIN DimProduct dp ON fis.ProductKey = dp.ProductKey
    INNER JOIN DimProductSubcategory psc ON dp.ProductSubcategoryKey = psc.ProductSubcategoryKey
    INNER JOIN DimProductCategory pc ON psc.ProductCategoryKey = pc.ProductCategoryKey
    WHERE fis.OrderDate BETWEEN @StartDate AND @EndDate
    GROUP BY pc.EnglishProductCategoryName
    ORDER BY TotalSales DESC;
END;
```

### BR1: Date-Range Filter (Inclusive)

- Input parameters: `@StartDate`, `@EndDate` (`DATE`).
- Rule: Only rows in `FactInternetSales` where `OrderDate` is between `@StartDate` and `@EndDate` (inclusive) are considered.

### BR2: Dimension Conformance

- Only rows that successfully join across these keys are included:
  - `FactInternetSales.ProductKey → DimProduct.ProductKey`
  - `DimProduct.ProductSubcategoryKey → DimProductSubcategory.ProductSubcategoryKey`
  - `DimProductSubcategory.ProductCategoryKey → DimProductCategory.ProductCategoryKey`
- Any missing foreign-key linkage implicitly excludes the row.

### BR3: Output Grain = Product Category

- Results are grouped by `DimProductCategory.EnglishProductCategoryName`.
- One row per product category.

### BR4: Aggregated Metrics per Category

For each product category, the following measures are produced:

- `TotalSales`  = `SUM(FactInternetSales.SalesAmount)`
- `TotalOrders` = `COUNT(FactInternetSales.SalesOrderNumber)`
- `AverageOrderValue` = `AVG(FactInternetSales.SalesAmount)`

### BR5: Business Ordering Rule

- Result set is ordered by `TotalSales` in **descending** order so the highest-revenue categories appear first.

## Python Module: `sales_summary_rules.py`

This module implements the above business rules in Python using `pandas`.

### Functions

#### `load_schema_metadata(path: str) -> pd.DataFrame`

- Loads `schema_metadata.xlsx` (or a compatible workbook) into a DataFrame.
- Expected columns include: `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`, `DATA_TYPE`, etc.

#### `validate_schema_for_sales_summary(schema_df: pd.DataFrame) -> None`

- Validates that the schema metadata contains all required columns for:
  - `dbo.FactInternetSales`
    - `SalesAmount`, `SalesOrderNumber`, `OrderDate`, `ProductKey`
  - `dbo.DimProduct`
    - `ProductKey`, `ProductSubcategoryKey`
  - `dbo.DimProductSubcategory`
    - `ProductSubcategoryKey`, `ProductCategoryKey`
  - `dbo.DimProductCategory`
    - `ProductCategoryKey`, `EnglishProductCategoryName`
- Raises a `ValueError` if any expected `(schema, table, column)` triple is missing.

Use this function before running the sales summary to ensure the underlying database structure matches expectations.

#### `calculate_sales_summary(...) -> pd.DataFrame`

Signature (simplified):

```python
calculate_sales_summary(
    fact_internet_sales: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_product_subcategory: pd.DataFrame,
    dim_product_category: pd.DataFrame,
    start_date,
    end_date,
) -> pd.DataFrame
```

Implements the logic of `usp_CalculateSalesSummary` in pandas:

1. **OrderDate coercion**
   - Converts `fact_internet_sales["OrderDate"]` to `datetime` via `pd.to_datetime`.
   - Accepts a variety of date string formats.

2. **Inclusive date filter**
   - Creates a mask where `OrderDate` is between `start_date` and `end_date` (inclusive).
   - Filters `FactInternetSales` accordingly.

3. **Joins through product dimensions**
   - Inner joins:
     - `FactInternetSales` with `DimProduct` on `ProductKey`.
     - That result with `DimProductSubcategory` on `ProductSubcategoryKey`.
     - That result with `DimProductCategory` on `ProductCategoryKey`.
   - Equivalent to the SQL `INNER JOIN` chain in the stored procedure.

4. **Aggregation and output**
   - Groups by `EnglishProductCategoryName`.
   - Computes:
     - `TotalSales` (sum of `SalesAmount`)
     - `TotalOrders` (count of `SalesOrderNumber`)
     - `AverageOrderValue` (mean of `SalesAmount`)
   - Renames `EnglishProductCategoryName` to `ProductCategory`.
   - Sorts descending by `TotalSales`.
   - Returns a tidy DataFrame with columns:

     - `ProductCategory`
     - `TotalSales`
     - `TotalOrders`
     - `AverageOrderValue`

5. **Empty-result handling**
   - If no rows remain after filtering/joining, returns an empty DataFrame with the expected columns.

#### `load_sample_database_log(path: str) -> pd.DataFrame`

- Helper to load `sampled_data.xlsx` which contains `DatabaseLog` history.
- This data is not used directly for the sales summary calculation but can be used for auditing object creations/changes.

## Test Module: `test_sales_summary_rules.py`

This file provides basic tests to validate the Python implementation.

### Tests

#### `test_validate_schema_with_metadata()`

- Loads `schema_metadata.xlsx` from the current working directory.
- Calls `validate_schema_for_sales_summary(schema)`.
- Passes silently if all required columns are present.
- Raises a `ValueError` with a clear message if requirements are not met.

#### `test_calculate_sales_summary_basic()`

- Builds small synthetic DataFrames mimicking:
  - `FactInternetSales`
  - `DimProduct`
  - `DimProductSubcategory`
  - `DimProductCategory`
- Runs `calculate_sales_summary` for a specific date range.
- Asserts expected:
  - Product categories (order by descending `TotalSales`).
  - TotalSales, TotalOrders, AverageOrderValue per category.

This ensures that the Python implementation matches the SQL business rules on a controlled example.

#### `run_all()`

- Convenience function that runs all tests in this module.
- The `__main__` block calls `run_all()` so the tests run when the script is executed directly.

## How to Run the Tests

From the repository root (`g:/Windsurf-POC-BLE/Windsurf-POC-BLE`):

1. (One-time) Install dependencies:

   ```bash
   pip install pandas openpyxl
   ```

2. Change to the BLE-SOURCE directory:

   ```bash
   cd BLE-SOURCE
   ```

3. Run the tests:

   ```bash
   python test_sales_summary_rules.py
   ```

- If everything is set up correctly, the script will exit without errors.
- If there is a problem with `schema_metadata.xlsx` or any of the expectations, you will receive a `ValueError` with details.

## Using the Business Rules in Other Code

A typical usage pattern in Python:

```python
import pandas as pd
from sales_summary_rules import (
    load_schema_metadata,
    validate_schema_for_sales_summary,
    calculate_sales_summary,
)

# 1. Validate schema
schema_df = load_schema_metadata("schema_metadata.xlsx")
validate_schema_for_sales_summary(schema_df)

# 2. Load your fact/dimension tables into DataFrames
# (from SQL, CSV, Excel, etc.)
fis_df = ...  # FactInternetSales
prod_df = ...  # DimProduct
psc_df = ...  # DimProductSubcategory
pc_df = ...  # DimProductCategory

# 3. Run the sales summary
summary_df = calculate_sales_summary(
    fis_df,
    prod_df,
    psc_df,
    pc_df,
    start_date="2013-01-01",
    end_date="2013-12-31",
)

print(summary_df)
```

## Notes and Limitations

- `sampled_data.xlsx` currently contains `DatabaseLog`-style rows, not the actual fact/dimension data needed for `calculate_sales_summary`. To run a full end-to-end numeric check, you will need to load/export:
  - `FactInternetSales`
  - `DimProduct`
- Date parsing is handled by `pandas.to_datetime`, which is robust but still dependent on well-formed input strings.
- This implementation focuses on replicating the behavior of `usp_CalculateSalesSummary`; it does not attempt to model additional business logic that might exist elsewhere in AdventureWorksDW.

## Extending This Work

Possible extensions:

- Add loaders to extract data directly from SQL Server (e.g., using `pyodbc` or `sqlalchemy`).
- Add more detailed tests, including edge cases for date ranges and missing dimension keys.
- Implement additional business rules from other stored procedures or views (e.g., `vDMPrep`, `vTargetMail`).
- Wrap the functionality in a CLI or scheduled job for automated validation or reporting.

## Synthetic Data Generator (`synthetic_sales_data.py`)

The module `synthetic_sales_data.py` creates small, self-contained dimension and fact tables that match the expectations of `calculate_sales_summary`. It supports both simple sample data and data with explicit seasonal patterns.

### Functions

- **`create_synthetic_dimensions() -> (dim_product, dim_product_subcategory, dim_product_category)`**
  - Builds in-memory DataFrames corresponding to:
    - `DimProductCategory` with three categories: *Bikes*, *Accessories*, *Clothing*.
    - `DimProductSubcategory` mapping subcategories (e.g. Road bikes, Helmets) to categories.
    - `DimProduct` mapping product keys to subcategories.
  - These structures are consistent with the joins used in `calculate_sales_summary`.

- **`create_synthetic_fact_internet_sales() -> pd.DataFrame`**
  - Creates a small `FactInternetSales`-like table with:
    - `ProductKey`
    - `OrderDate`
    - `SalesAmount`
    - `SalesOrderNumber`
  - Contains a handful of rows across Bikes, Accessories, and Clothing, including one row outside the target date range to test filtering.

- **`create_synthetic_fact_internet_sales_with_seasonality(year: int = 2013) -> pd.DataFrame`**
  - Generates a full year of sales with **seasonal effects** per month and category:
    - **Bikes**: low in winter (Jan–Feb, Nov–Dec), peak in late spring/summer (May–Aug).
    - **Accessories**: relatively stable with a modest summer bump.
    - **Clothing**: lower in spring/summer, strong peak in Q4 and higher levels in winter months.
  - For each month and product key, it:
    - Maps the product to a category (`Bikes`, `Accessories`, `Clothing`).
    - Applies a category-specific base ticket size and a month-specific seasonal multiplier.
    - Creates an order with an `OrderDate` within that month and a corresponding `SalesAmount`.
  - The resulting DataFrame can be passed directly into `calculate_sales_summary`.

- **`export_synthetic_to_csv(prefix: str = "synthetic_")`**
  - Writes non-seasonal synthetic tables to CSV files in the current directory using the given prefix:
    - `<prefix>DimProduct.csv`
    - `<prefix>DimProductSubcategory.csv`
    - `<prefix>DimProductCategory.csv`
    - `<prefix>FactInternetSales.csv`

- **`export_synthetic_with_seasonality_to_csv(year: int = 2013, prefix: str = "synthetic_seasonal_")`**
  - Writes seasonal synthetic tables to CSV files in the current directory:
    - `synthetic_seasonal_DimProduct.csv`
    - `synthetic_seasonal_DimProductSubcategory.csv`
    - `synthetic_seasonal_DimProductCategory.csv`
    - `synthetic_seasonal_FactInternetSales.csv`
  - Uses the same dimensions as `create_synthetic_dimensions` and a seasonality-aware fact table.

### How the Synthetic Generator Is Structured

- **Dimension first, then fact**
  - Dimensions (`DimProduct`, `DimProductSubcategory`, `DimProductCategory`) are created once and reused across non-seasonal and seasonal fact generations.
  - This ensures that all foreign-key relationships expected by `calculate_sales_summary` are valid.

- **Category-level seasonality**
  - The seasonal generator associates each `ProductKey` with a conceptual category.
  - For each category, it defines a set of monthly multipliers that shape sales over the year.
  - `SalesAmount` is computed as `base_amount[category] * seasonal_factor[month]`, giving predictable patterns in the aggregated results.

- **Deterministic**
  - No randomness is used; the same inputs always produce the same synthetic dataset, which is useful for repeatable tests and demos.

### Using the Synthetic Generator from Python

Example: generate seasonal data in memory and run the sales summary:

```python
import synthetic_sales_data as synth
from sales_summary_rules import calculate_sales_summary

# 1. Create synthetic dimensions and seasonal fact data
dim_product, dim_psc, dim_pc = synth.create_synthetic_dimensions()
fact = synth.create_synthetic_fact_internet_sales_with_seasonality(year=2013)

# 2. Run the business rules
summary = calculate_sales_summary(
    fact,
    dim_product,
    dim_psc,
    dim_pc,
    start_date="2013-01-01",
    end_date="2013-12-31",
)

print(summary)
```

### Generating CSV Files from the Command Line

From `BLE-SOURCE` you can generate CSV files for inspection or reuse.

- **Non-seasonal synthetic data**

  ```bash
  python -c "import synthetic_sales_data as s; s.export_synthetic_to_csv()"
  ```

- **Seasonal synthetic data**

  ```bash
  python -c "import synthetic_sales_data as s; s.export_synthetic_with_seasonality_to_csv(year=2013)"
  ```

The generated CSVs can then be loaded with `pandas.read_csv` and passed directly into `calculate_sales_summary` for end-to-end testing and demonstration of the business rules under controlled synthetic workloads.

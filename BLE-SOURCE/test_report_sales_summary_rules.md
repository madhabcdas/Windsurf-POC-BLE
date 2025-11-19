# Test Report: sales_summary_rules

## Overview

- **Date**: 2025-11-20
- **Location**: `BLE-SOURCE` directory
- **Command executed**:
  ```bash
  python test_sales_summary_rules.py
  ```
- **Exit code**: 0 (success)

## Tests Executed

1. **test_validate_schema_with_metadata**
   - **Description**: Loads `schema_metadata.xlsx` and validates that all required tables and columns exist for the sales summary business rules.
   - **Result**: Passed (no `ValueError` raised).

2. **test_calculate_sales_summary_basic**
   - **Description**: Uses synthetic DataFrames for `FactInternetSales`, `DimProduct`, `DimProductSubcategory`, and `DimProductCategory` to verify that the Python implementation of `usp_CalculateSalesSummary`:
     - Filters by the specified date range.
     - Joins across the product dimensions correctly.
     - Aggregates and orders the results per product category as expected.
   - **Result**: Passed (all assertions on categories, `TotalSales`, `TotalOrders`, and `AverageOrderValue` matched expected values).

## Summary

All tests in `test_sales_summary_rules.py` completed successfully with exit code 0.

The Python implementation in `sales_summary_rules.py` is currently consistent with the tested business rules derived from the SQL stored procedure `dbo.usp_CalculateSalesSummary`.

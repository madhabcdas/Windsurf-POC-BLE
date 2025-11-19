import pandas as pd

# Business rules translated from dbo.usp_CalculateSalesSummary
# - Filter FactInternetSales rows by inclusive OrderDate range
# - Join to DimProduct, DimProductSubcategory, DimProductCategory
# - Group by EnglishProductCategoryName
# - Compute SUM(SalesAmount), COUNT(SalesOrderNumber), AVG(SalesAmount)
# - Order by TotalSales DESC

_REQUIRED_COLUMNS = [
    ("dbo", "FactInternetSales", "SalesAmount"),
    ("dbo", "FactInternetSales", "SalesOrderNumber"),
    ("dbo", "FactInternetSales", "OrderDate"),
    ("dbo", "FactInternetSales", "ProductKey"),
    ("dbo", "DimProduct", "ProductKey"),
    ("dbo", "DimProduct", "ProductSubcategoryKey"),
    ("dbo", "DimProductSubcategory", "ProductSubcategoryKey"),
    ("dbo", "DimProductSubcategory", "ProductCategoryKey"),
    ("dbo", "DimProductCategory", "ProductCategoryKey"),
    ("dbo", "DimProductCategory", "EnglishProductCategoryName"),
]


def load_schema_metadata(path: str) -> pd.DataFrame:
    """Load schema metadata from the provided Excel file."""

    return pd.read_excel(path)


def validate_schema_for_sales_summary(schema_df: pd.DataFrame) -> None:
    """Validate that schema metadata contains all columns needed by the procedure."""

    required_meta_cols = {"TABLE_SCHEMA", "TABLE_NAME", "COLUMN_NAME"}
    missing_meta_cols = required_meta_cols - set(schema_df.columns)
    if missing_meta_cols:
        raise ValueError(
            "Schema metadata missing columns: " + ", ".join(sorted(missing_meta_cols))
        )

    def has_row(schema: str, table: str, column: str) -> bool:
        mask = (
            schema_df["TABLE_SCHEMA"].str.lower().eq(schema.lower())
            & schema_df["TABLE_NAME"].str.lower().eq(table.lower())
            & schema_df["COLUMN_NAME"].str.lower().eq(column.lower())
        )
        return bool(mask.any())

    missing_reqs = [
        (s, t, c) for (s, t, c) in _REQUIRED_COLUMNS if not has_row(s, t, c)
    ]
    if missing_reqs:
        names = [f"{s}.{t}.{c}" for (s, t, c) in missing_reqs]
        raise ValueError(
            "Schema metadata is missing required columns for sales summary: "
            + ", ".join(names)
        )


def calculate_sales_summary(
    fact_internet_sales: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_product_subcategory: pd.DataFrame,
    dim_product_category: pd.DataFrame,
    start_date,
    end_date,
) -> pd.DataFrame:
    """Replicate dbo.usp_CalculateSalesSummary in pandas."""

    fis = fact_internet_sales.copy()
    fis["OrderDate"] = pd.to_datetime(fis["OrderDate"])
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)

    mask = (fis["OrderDate"] >= start_ts) & (fis["OrderDate"] <= end_ts)
    fis = fis.loc[mask]

    merged = fis.merge(
        dim_product[["ProductKey", "ProductSubcategoryKey"]],
        on="ProductKey",
        how="inner",
    ).merge(
        dim_product_subcategory[["ProductSubcategoryKey", "ProductCategoryKey"]],
        on="ProductSubcategoryKey",
        how="inner",
    ).merge(
        dim_product_category[["ProductCategoryKey", "EnglishProductCategoryName"]],
        on="ProductCategoryKey",
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(
            columns=[
                "ProductCategory",
                "TotalSales",
                "TotalOrders",
                "AverageOrderValue",
            ]
        )

    grouped = (
        merged.groupby("EnglishProductCategoryName", as_index=False)
        .agg(
            TotalSales=("SalesAmount", "sum"),
            TotalOrders=("SalesOrderNumber", "count"),
            AverageOrderValue=("SalesAmount", "mean"),
        )
        .rename(columns={"EnglishProductCategoryName": "ProductCategory"})
        .sort_values("TotalSales", ascending=False)
        .reset_index(drop=True)
    )

    return grouped


def load_sample_database_log(path: str) -> pd.DataFrame:
    """Load the provided sampled_data.xlsx (DatabaseLog snapshot).

    Note: this file contains DDL event logs, not FactInternetSales data. It is
    useful for auditing but is not used directly in calculate_sales_summary.
    """

    return pd.read_excel(path)

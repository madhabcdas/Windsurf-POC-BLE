import pandas as pd
from datetime import datetime


def create_synthetic_dimensions() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create synthetic DimProduct, DimProductSubcategory, DimProductCategory tables.

    Returns:
        dim_product, dim_product_subcategory, dim_product_category
    """

    dim_product_category = pd.DataFrame(
        [
            {"ProductCategoryKey": 1, "EnglishProductCategoryName": "Bikes"},
            {"ProductCategoryKey": 2, "EnglishProductCategoryName": "Accessories"},
            {"ProductCategoryKey": 3, "EnglishProductCategoryName": "Clothing"},
        ]
    )

    dim_product_subcategory = pd.DataFrame(
        [
            {"ProductSubcategoryKey": 10, "ProductCategoryKey": 1},  # Road bikes
            {"ProductSubcategoryKey": 11, "ProductCategoryKey": 1},  # Mountain bikes
            {"ProductSubcategoryKey": 20, "ProductCategoryKey": 2},  # Helmets
            {"ProductSubcategoryKey": 21, "ProductCategoryKey": 2},  # Gloves
            {"ProductSubcategoryKey": 30, "ProductCategoryKey": 3},  # Jerseys
        ]
    )

    dim_product = pd.DataFrame(
        [
            {"ProductKey": 1000, "ProductSubcategoryKey": 10},
            {"ProductKey": 1001, "ProductSubcategoryKey": 10},
            {"ProductKey": 1010, "ProductSubcategoryKey": 11},
            {"ProductKey": 2000, "ProductSubcategoryKey": 20},
            {"ProductKey": 2001, "ProductSubcategoryKey": 21},
            {"ProductKey": 3000, "ProductSubcategoryKey": 30},
        ]
    )

    return dim_product, dim_product_subcategory, dim_product_category


def create_synthetic_fact_internet_sales() -> pd.DataFrame:
    """Create a small synthetic FactInternetSales-like table.

    Columns used by calculate_sales_summary:
        - ProductKey
        - OrderDate
        - SalesAmount
        - SalesOrderNumber
    """

    rows = [
        # Bikes (Road) in Jan
        {"ProductKey": 1000, "OrderDate": datetime(2013, 1, 1), "SalesAmount": 500.0, "SalesOrderNumber": "SO100"},
        {"ProductKey": 1000, "OrderDate": datetime(2013, 1, 3), "SalesAmount": 750.0, "SalesOrderNumber": "SO101"},
        {"ProductKey": 1001, "OrderDate": datetime(2013, 1, 15), "SalesAmount": 300.0, "SalesOrderNumber": "SO102"},
        # Bikes (Mountain) in Feb
        {"ProductKey": 1010, "OrderDate": datetime(2013, 2, 5), "SalesAmount": 900.0, "SalesOrderNumber": "SO103"},
        # Accessories (Helmets & Gloves) in Jan-Feb
        {"ProductKey": 2000, "OrderDate": datetime(2013, 1, 10), "SalesAmount": 80.0, "SalesOrderNumber": "SO200"},
        {"ProductKey": 2000, "OrderDate": datetime(2013, 2, 12), "SalesAmount": 120.0, "SalesOrderNumber": "SO201"},
        {"ProductKey": 2001, "OrderDate": datetime(2013, 2, 20), "SalesAmount": 60.0, "SalesOrderNumber": "SO202"},
        # Clothing (Jerseys) in Jan, plus one row outside range (2012)
        {"ProductKey": 3000, "OrderDate": datetime(2013, 1, 25), "SalesAmount": 45.0, "SalesOrderNumber": "SO300"},
        {"ProductKey": 3000, "OrderDate": datetime(2012, 12, 31), "SalesAmount": 999.0, "SalesOrderNumber": "SO301"},
    ]

    return pd.DataFrame(rows)


def create_synthetic_fact_internet_sales_with_seasonality(year: int = 2013) -> pd.DataFrame:
    """Create synthetic FactInternetSales-like data with simple seasonal effects.

    Seasonality model (per product category):
        - Bikes: peak in late spring/summer, low in winter.
        - Accessories: relatively stable with a mild summer bump.
        - Clothing: strong peak in Q4 and higher in winter months.
    """

    # Map product keys to conceptual categories for seasonality
    product_category = {
        1000: "Bikes",
        1001: "Bikes",
        1010: "Bikes",
        2000: "Accessories",
        2001: "Accessories",
        3000: "Clothing",
    }

    # Base ticket size per category
    base_amount = {
        "Bikes": 600.0,
        "Accessories": 60.0,
        "Clothing": 45.0,
    }

    # Monthly seasonal multipliers per category
    seasonal_factors = {
        "Bikes": {
            1: 0.5,
            2: 0.6,
            3: 0.8,
            4: 1.1,
            5: 1.3,
            6: 1.5,
            7: 1.6,
            8: 1.4,
            9: 1.1,
            10: 0.9,
            11: 0.6,
            12: 0.5,
        },
        "Accessories": {
            1: 0.9,
            2: 0.9,
            3: 1.0,
            4: 1.0,
            5: 1.1,
            6: 1.1,
            7: 1.1,
            8: 1.0,
            9: 1.0,
            10: 1.0,
            11: 0.9,
            12: 0.9,
        },
        "Clothing": {
            1: 1.3,
            2: 1.2,
            3: 1.0,
            4: 0.7,
            5: 0.5,
            6: 0.5,
            7: 0.6,
            8: 0.7,
            9: 0.9,
            10: 1.2,
            11: 1.5,
            12: 1.7,
        },
    }

    rows: list[dict] = []
    products = sorted(product_category.keys())

    for month in range(1, 13):
        for idx, product_key in enumerate(products, start=1):
            category = product_category[product_key]
            factor = seasonal_factors[category][month]
            amount = base_amount[category] * factor

            # Simple day-of-month spread; stays within [1, 28]
            day = min(3 * idx, 28)
            order_date = datetime(year, month, day)
            order_number = f"SO-{year}{month:02d}-{product_key}-{idx}"

            rows.append(
                {
                    "ProductKey": product_key,
                    "OrderDate": order_date,
                    "SalesAmount": round(amount, 2),
                    "SalesOrderNumber": order_number,
                }
            )

    return pd.DataFrame(rows)


def export_synthetic_to_csv(prefix: str = "synthetic_") -> None:
    """Export synthetic fact and dimension tables to CSV files in the current directory."""

    dim_product, dim_product_subcategory, dim_product_category = create_synthetic_dimensions()
    fact = create_synthetic_fact_internet_sales()

    dim_product.to_csv(f"{prefix}DimProduct.csv", index=False)
    dim_product_subcategory.to_csv(f"{prefix}DimProductSubcategory.csv", index=False)
    dim_product_category.to_csv(f"{prefix}DimProductCategory.csv", index=False)
    fact.to_csv(f"{prefix}FactInternetSales.csv", index=False)


def export_synthetic_with_seasonality_to_csv(
    year: int = 2013, prefix: str = "synthetic_seasonal_",
) -> None:
    """Export seasonal synthetic tables to CSV files in the current directory."""

    dim_product, dim_product_subcategory, dim_product_category = create_synthetic_dimensions()
    fact = create_synthetic_fact_internet_sales_with_seasonality(year=year)

    dim_product.to_csv(f"{prefix}DimProduct.csv", index=False)
    dim_product_subcategory.to_csv(f"{prefix}DimProductSubcategory.csv", index=False)
    dim_product_category.to_csv(f"{prefix}DimProductCategory.csv", index=False)
    fact.to_csv(f"{prefix}FactInternetSales.csv", index=False)


if __name__ == "__main__":  # manual generation helper
    export_synthetic_to_csv()

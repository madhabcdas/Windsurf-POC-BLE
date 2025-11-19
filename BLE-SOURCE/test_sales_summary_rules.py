import pandas as pd
import pytest

from sales_summary_rules import (
    load_schema_metadata,
    validate_schema_for_sales_summary,
    calculate_sales_summary,
)


def test_validate_schema_with_metadata() -> None:
    schema = load_schema_metadata("schema_metadata.xlsx")
    validate_schema_for_sales_summary(schema)


def test_calculate_sales_summary_basic() -> None:
    fact_internet_sales = pd.DataFrame(
        [
            {"ProductKey": 1000, "OrderDate": "2013-01-01", "SalesAmount": 100.0, "SalesOrderNumber": "SO1"},
            {"ProductKey": 1000, "OrderDate": "2013-01-02", "SalesAmount": 150.0, "SalesOrderNumber": "SO2"},
            {"ProductKey": 1001, "OrderDate": "2013-01-02", "SalesAmount": 200.0, "SalesOrderNumber": "SO3"},
            {"ProductKey": 2000, "OrderDate": "2013-01-02", "SalesAmount": 50.0, "SalesOrderNumber": "SO4"},
            {"ProductKey": 1000, "OrderDate": "2012-12-31", "SalesAmount": 999.0, "SalesOrderNumber": "SOX"},
        ]
    )

    dim_product = pd.DataFrame(
        [
            {"ProductKey": 1000, "ProductSubcategoryKey": 100},
            {"ProductKey": 1001, "ProductSubcategoryKey": 100},
            {"ProductKey": 2000, "ProductSubcategoryKey": 200},
        ]
    )

    dim_product_subcategory = pd.DataFrame(
        [
            {"ProductSubcategoryKey": 100, "ProductCategoryKey": 1},
            {"ProductSubcategoryKey": 200, "ProductCategoryKey": 2},
        ]
    )

    dim_product_category = pd.DataFrame(
        [
            {"ProductCategoryKey": 1, "EnglishProductCategoryName": "Bikes"},
            {"ProductCategoryKey": 2, "EnglishProductCategoryName": "Accessories"},
        ]
    )

    result = calculate_sales_summary(
        fact_internet_sales,
        dim_product,
        dim_product_subcategory,
        dim_product_category,
        start_date="2013-01-01",
        end_date="2013-01-31",
    )

    assert list(result["ProductCategory"]) == ["Bikes", "Accessories"]
    assert list(result["TotalSales"]) == [450.0, 50.0]
    assert list(result["TotalOrders"]) == [3, 1]
    assert list(result["AverageOrderValue"]) == [150.0, 50.0]


def test_validate_schema_negative_missing_metadata_column() -> None:
    schema = pd.DataFrame(
        [
            {"TABLE_SCHEMA": "dbo", "TABLE_NAME": "FactInternetSales"},
        ]
    )
    with pytest.raises(ValueError):
        validate_schema_for_sales_summary(schema)


def test_validate_schema_negative_missing_required_column() -> None:
    schema = pd.DataFrame(
        [
            {
                "TABLE_SCHEMA": "dbo",
                "TABLE_NAME": "FactInternetSales",
                "COLUMN_NAME": "SalesAmount",
            }
        ]
    )

    with pytest.raises(ValueError):
        validate_schema_for_sales_summary(schema)


@pytest.mark.parametrize(
    "schema",
    [
        pd.DataFrame(
            [
                {"TABLE_SCHEMA": "dbo", "TABLE_NAME": "FactInternetSales"},
            ]
        ),
        pd.DataFrame(
            [
                {
                    "TABLE_SCHEMA": "dbo",
                    "TABLE_NAME": "FactInternetSales",
                    "COLUMN_NAME": "SalesAmount",
                }
            ]
        ),
    ],
)
def test_validate_schema_negative_parametrized(schema: pd.DataFrame) -> None:
    """Parametrized negative cases for schema validation using pytest."""

    with pytest.raises(ValueError):
        validate_schema_for_sales_summary(schema)


def test_calculate_sales_summary_negative_all_outside_range() -> None:
    fact_internet_sales = pd.DataFrame(
        [
            {"ProductKey": 1000, "OrderDate": "2012-01-01", "SalesAmount": 100.0, "SalesOrderNumber": "SO1"},
            {"ProductKey": 1001, "OrderDate": "2012-01-02", "SalesAmount": 150.0, "SalesOrderNumber": "SO2"},
        ]
    )

    dim_product = pd.DataFrame(
        [
            {"ProductKey": 1000, "ProductSubcategoryKey": 100},
            {"ProductKey": 1001, "ProductSubcategoryKey": 100},
        ]
    )

    dim_product_subcategory = pd.DataFrame(
        [
            {"ProductSubcategoryKey": 100, "ProductCategoryKey": 1},
        ]
    )

    dim_product_category = pd.DataFrame(
        [
            {"ProductCategoryKey": 1, "EnglishProductCategoryName": "Bikes"},
        ]
    )

    result = calculate_sales_summary(
        fact_internet_sales,
        dim_product,
        dim_product_subcategory,
        dim_product_category,
        start_date="2013-01-01",
        end_date="2013-01-31",
    )

    assert result.empty
    assert list(result.columns) == [
        "ProductCategory",
        "TotalSales",
        "TotalOrders",
        "AverageOrderValue",
    ]


def test_calculate_sales_summary_negative_bad_orderdate() -> None:
    fact_internet_sales = pd.DataFrame(
        [
            {"ProductKey": 1000, "OrderDate": "not-a-date", "SalesAmount": 100.0, "SalesOrderNumber": "SO1"},
        ]
    )

    dim_product = pd.DataFrame([
        {"ProductKey": 1000, "ProductSubcategoryKey": 100},
    ])

    dim_product_subcategory = pd.DataFrame([
        {"ProductSubcategoryKey": 100, "ProductCategoryKey": 1},
    ])

    dim_product_category = pd.DataFrame([
        {"ProductCategoryKey": 1, "EnglishProductCategoryName": "Bikes"},
    ])

    with pytest.raises(Exception):
        calculate_sales_summary(
            fact_internet_sales,
            dim_product,
            dim_product_subcategory,
            dim_product_category,
            start_date="2013-01-01",
            end_date="2013-01-31",
        )


def run_all() -> None:
    test_validate_schema_with_metadata()
    test_calculate_sales_summary_basic()
    test_validate_schema_negative_missing_metadata_column()
    test_validate_schema_negative_missing_required_column()
    test_calculate_sales_summary_negative_all_outside_range()
    test_calculate_sales_summary_negative_bad_orderdate()


if __name__ == "__main__":
    run_all()

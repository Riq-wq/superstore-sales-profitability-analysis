# Superstore Sales & Profitability Analysis

End-to-end data analytics pipeline on the Sample Superstore dataset — cleaned with Python/Pandas, loaded into MySQL, queried for business insights, and visualized in an interactive Power BI dashboard.

## Overview

This project analyzes 5,009 orders (9,994 line items) from the Sample Superstore dataset to uncover what's actually driving — and draining — profitability across categories, discount levels, regions, and customer segments. The standout finding: profitability turns negative as soon as discounts pass the **20% mark**, giving a clear, data-backed rule for future pricing decisions.

**Pipeline:** `Python (Pandas) → MySQL → SQL analysis → Power BI dashboard → PDF report`

## Key Insights

-  **$2.30M** total sales, **$286.4K** total profit, **12.47%** overall margin
-  Profit margin turns negative once discounts pass **20%** — the 21–40% band averages **-16.7%**, and orders discounted 40%+ lose money at a **-108.9%** average margin (mean of per-order margins within each band)
-  **Furniture** generates nearly as much revenue as Office Supplies but returns 6–8x less profit
-  Ten states — led by **Texas** and **Ohio** — are net loss-making despite solid sales volume
- 📅 Clear seasonality, with **Sept–Dec** consistently the strongest months for sales and profit

## Repository Contents

| File | Description |
|------|--------------|
| `notebooks/Superstore.ipynb` | Data cleaning & feature engineering notebook (Pandas) |
| `data/Superstore_cleaned.csv` | Cleaned dataset, ready for MySQL/BI tools |
| `sql/superstore queries.sql` | 10 business insight SQL queries against the MySQL `orders` table |
| `dashboard/superstore dashboard.pbix` | 3-page interactive Power BI dashboard |
| `report/Superstore_Sales_Profitability_Report.pdf` | Full written report with charts and recommendations |

## Data Cleaning (Python/Pandas)

- Verified there were no duplicate rows to remove
- Converted `Order Date` / `Ship Date` to proper datetime types
- Cast `Postal Code` to 5-digit text, restoring leading zeros that were lost when read as a number
- Trimmed whitespace across all text columns
- Standardized all column names to `snake_case`
- Engineered new features: `shipping_duration`, `profit_margin` (%), `cost`, and an `is_loss` flag
- Loaded the cleaned data into MySQL as the `orders` table for SQL analysis

## SQL Analysis

Ten queries answer core business questions, including:
- Overall sales, profit, and margin
- Category & sub-category profitability
- Discount level vs. profitability
- State & regional performance
- Customer segment value
- Shipping mode vs. margin
- Monthly sales seasonality

See superstore queries.sql for the full set, each with an inline comment explaining the business question it answers.

## Power BI Dashboard

A 3-page interactive dashboard built on the cleaned dataset:

![Superstore Sales & Profitability Dashboard — Overview](assets/dashboard.png)

1. **Overview** — KPI cards, sales & profit by category, segment split, monthly trend
2. **Profitability Deep-Dive** — sub-category profit ranking, discount vs. margin, discount band analysis
3. **Regional & Operational Performance** — state/region profitability table, shipping mode analysis, top customers

## Recommendations

- Cap discounts at 20% on Furniture and Office Supplies orders
- Review Furniture pricing, particularly Tables and Bookcases
- Investigate Texas and Ohio operations for region-specific discounting or cost issues
- Plan promotions and inventory around the Sep–Dec peak season

## Tools Used

`Python` · `Pandas` · `SQLAlchemy` · `MySQL` · `Power BI` · `DAX`

## Author

**Hassan Jumaa (Riq)**
Data Analyst | [Portfolio](https://riq-wq.github.io/Myportfolio) · [LinkedIn](https://linkedin.com/in/mrisa-juma-56a600416) · [GitHub](https://github.com/Riq-wq)

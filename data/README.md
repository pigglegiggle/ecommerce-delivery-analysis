# Olist Dataset Guide

## Source and time period

- **Source:** [Brazilian E-Commerce Public Dataset by Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- The data covers Brazilian marketplace orders from 2016 to 2018.
- The Kaggle archive contains nine CSV tables. The analysis uses three: orders, customers, and reviews.
- Run `python src/download_data.py` to download the archive and save those three tables in `data/raw/`.

## Tables used in this project

| CSV table | What it contains | Fields used |
|---|---|---|
| `olist_orders_dataset.csv` | One row per order, with its status and timestamps | `order_id`, `customer_id`, `order_status`, `order_delivered_customer_date`, `order_estimated_delivery_date` |
| `olist_customers_dataset.csv` | Customer ID and location for each order | `customer_id`, `customer_state` |
| `olist_order_reviews_dataset.csv` | Customer ratings and optional written comments | `order_id`, `review_score` |

Join the orders and customers tables on `customer_id`. Join reviews to orders on `order_id`. An order can have more than one review row, so the analysis averages review scores by order before joining. That keeps each delivery counted once.

## The other tables in the Kaggle archive

| CSV table | What it contains |
|---|---|
| `olist_order_items_dataset.csv` | Products in each order, including seller, price, and shipping limit. Each row is one product added to an order. |
| `olist_order_payments_dataset.csv` | Payment method, number of installments, and payment amount for each order. |
| `olist_products_dataset.csv` | Product category, size, weight, and other product details. |
| `olist_sellers_dataset.csv` | Seller IDs and locations. |
| `olist_geolocation_dataset.csv` | Latitude and longitude for Brazilian postal-code prefixes. |
| `product_category_name_translation.csv` | Portuguese product-category names and their English translations. |

## Fields used for this analysis

| Field | Table | Meaning |
|---|---|---|
| `order_id` | Orders, reviews | Order number used to connect delivery dates and customer ratings |
| `customer_id` | Orders, customers | Customer number used to find the customer's state |
| `order_status` | Orders | Current status recorded for the order |
| `order_delivered_customer_date` | Orders | Date the customer received the order |
| `order_estimated_delivery_date` | Orders | Estimated delivery date |
| `customer_state` | Customers | Brazilian state code for the customer |
| `review_score` | Reviews | Customer rating from 1 to 5 |

The analysis includes delivered orders with both delivery dates. A delivery is late when its actual date is after its estimated date. See the [project README](../README.md) for the questions, results, charts, and SQL queries.

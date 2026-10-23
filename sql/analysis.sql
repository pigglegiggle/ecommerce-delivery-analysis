-- DuckDB. Run from projects/03-ecommerce-delivery.
-- Each row in delivery_analysis represents one delivered order.

CREATE OR REPLACE VIEW delivery_analysis AS
WITH review_by_order AS (
    SELECT order_id,
           AVG(TRY_CAST(review_score AS DOUBLE)) AS review_score
    FROM read_csv_auto('data/raw/olist_order_reviews_dataset.csv', header = true, all_varchar = true)
    GROUP BY order_id
), order_dates AS (
    SELECT o.order_id,
           o.customer_id,
           c.customer_state,
           TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP) AS delivered_at,
           TRY_CAST(o.order_estimated_delivery_date AS TIMESTAMP) AS expected_at,
           r.review_score
    FROM read_csv_auto('data/raw/olist_orders_dataset.csv', header = true, all_varchar = true) AS o
    LEFT JOIN read_csv_auto('data/raw/olist_customers_dataset.csv', header = true, all_varchar = true) AS c
      ON o.customer_id = c.customer_id
    LEFT JOIN review_by_order AS r
      ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
), delivery_days AS (
    SELECT *,
           DATE_DIFF('second', expected_at, delivered_at) / 86400.0 AS days_late
    FROM order_dates
    WHERE delivered_at IS NOT NULL AND expected_at IS NOT NULL
)
SELECT *,
       CASE WHEN days_late <= 0 THEN 'On time'
            WHEN days_late <= 7 THEN '1–7 days late'
            ELSE '8+ days late' END AS delivery_timing
FROM delivery_days;

-- Q1. Orders, late deliveries, late-delivery rate, and average review.
SELECT COUNT(*) AS delivered_orders,
       SUM(CASE WHEN days_late > 0 THEN 1 ELSE 0 END) AS late_deliveries,
       AVG(CASE WHEN days_late > 0 THEN 1.0 ELSE 0.0 END) AS late_delivery_rate,
       AVG(review_score) AS average_review_score
FROM delivery_analysis;

-- Q2. Average review score by delivery timing.
SELECT delivery_timing,
       COUNT(review_score) AS reviewed_orders,
       AVG(review_score) AS average_review_score
FROM delivery_analysis
GROUP BY delivery_timing
ORDER BY CASE delivery_timing
             WHEN 'On time' THEN 1
             WHEN '1–7 days late' THEN 2
             ELSE 3
         END;

-- Q3. States with the most late deliveries.
SELECT customer_state,
       SUM(CASE WHEN days_late > 0 THEN 1 ELSE 0 END) AS late_deliveries,
       COUNT(*) AS delivered_orders
FROM delivery_analysis
GROUP BY customer_state
ORDER BY late_deliveries DESC
LIMIT 10;

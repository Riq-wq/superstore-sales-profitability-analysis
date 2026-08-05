-- What is our total revenue, total profit, and overall profit margin?
select  round(sum(sales),2) as total_revenue,round(sum(profit),2) as total_profit,round(avg(profit_margin),2) as overall_profitmargin, COUNT(*) AS total_orders from orders;

-- Which product categories are the most and least profitable?
select  category,sum(profit) as total_profit  from  orders group by category order by total_profit desc;

-- Within each category, which sub-categories are actually losing money?
select category,sub_category,SUM(profit) AS total_loss FROM orders WHERE is_loss = TRUE GROUP BY category, sub_category;

-- Is there a relationship between discount level and profitability?
Select  discount,ROUND(AVG(profit), 2) AS avg_profit,ROUND(SUM(profit), 2) AS total_profit,COUNT(*) AS total_order
FROM orders GROUP BY discount ORDER BY discount;

-- Which states generate the most sales, and which are actually unprofitable?
SELECT state,ROUND(SUM(sales), 2) AS total_sales,ROUND(SUM(profit), 2) AS total_profit,COUNT(*) AS order_count
FROM orders GROUP BY state ORDER BY total_profit ASC LIMIT 10;


-- How do the four regions compare in sales, profit, and order volume?
SELECT region,ROUND(SUM(sales), 2) AS total_sales,ROUND(SUM(profit), 2) AS total_profit,COUNT(*) AS total_orders,
ROUND(SUM(sales) / COUNT(*), 2) AS avg_order_value FROM orders GROUP BY region ORDER BY total_profit DESC;


-- Which customer segment (Consumer, Corporate, Home Office) is most valuable?
SELECT segment,ROUND(SUM(sales), 2) AS total_sales,ROUND(SUM(profit), 2) AS total_profit,ROUND(AVG(profit_margin), 2) AS avg_profit_margin_pct
FROM orders GROUP BY segment ORDER BY total_profit DESC;



-- Who are our highest-value customers by total spend?
SELECT customer_name,COUNT(DISTINCT order_id) AS num_orders,ROUND(SUM(sales), 2) AS total_sales,ROUND(SUM(profit), 2) AS total_profit
FROM orders GROUP BY customer_name ORDER BY total_sales DESC LIMIT 10;

-- Does the shipping method chosen affect profit margins?
SELECT ship_mode,COUNT(*) AS order_count, ROUND(AVG(shipping_duration), 1) AS avg_shipping_days,ROUND(SUM(profit), 2) AS total_profit,
ROUND(AVG(profit_margin), 2) AS avg_profit_margin_pct FROM orders GROUP BY ship_mode ORDER BY total_profit DESC;

-- Is there a seasonal pattern in sales over the year?
SELECT MONTH(order_date) AS order_month, COUNT(*) AS total_orders,ROUND(SUM(sales), 2) AS total_sales,
ROUND(SUM(profit), 2) AS total_profit FROM orders GROUP BY MONTH(order_date)ORDER BY order_month;
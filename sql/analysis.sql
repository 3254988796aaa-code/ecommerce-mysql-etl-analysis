-- Run in a session using the intended database; choose a batch explicitly.
SET @dataset = (SELECT dataset_sha256 FROM dataset_batch ORDER BY imported_at DESC, dataset_sha256 LIMIT 1);

SELECT COUNT(*) AS feature_records, SUM(occurrence_count) AS source_observations,
       COUNT(DISTINCT keyword) AS keyword_count, MIN(product_price) AS min_price,
       MAX(product_price) AS max_price, AVG(product_price) AS mean_price
FROM product_observation WHERE dataset_sha256=@dataset;

SELECT keyword,COUNT(*) AS feature_records,AVG(product_price) AS mean_price,
       SUM(payment_count) AS displayed_payment_count_sum
FROM product_observation WHERE dataset_sha256=@dataset
GROUP BY keyword ORDER BY feature_records DESC,keyword LIMIT 20;

WITH ranked AS (
    SELECT keyword,product_name,product_price,payment_count,
        ROW_NUMBER() OVER (PARTITION BY keyword ORDER BY payment_count DESC,observation_hash) AS row_num
    FROM product_observation WHERE dataset_sha256=@dataset
)
SELECT keyword,product_name,product_price,payment_count FROM ranked WHERE row_num<=3;

SELECT price_band,COUNT(*) AS feature_records FROM (
    SELECT CASE WHEN product_price<50 THEN '[0,50)'
                WHEN product_price<100 THEN '[50,100)'
                WHEN product_price<200 THEN '[100,200)'
                WHEN product_price<500 THEN '[200,500)'
                ELSE '[500,+inf)' END AS price_band
    FROM product_observation WHERE dataset_sha256=@dataset
) classified GROUP BY price_band;

SELECT observation_hash,keyword,product_name,occurrence_count
FROM product_observation WHERE dataset_sha256=@dataset AND occurrence_count>1
ORDER BY occurrence_count DESC,observation_hash;

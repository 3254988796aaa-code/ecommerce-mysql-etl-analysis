CREATE TABLE IF NOT EXISTS dataset_batch (
    dataset_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    input_observations INT UNSIGNED NOT NULL,
    valid_observations INT UNSIGNED NOT NULL,
    feature_records INT UNSIGNED NOT NULL,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_observation (
    dataset_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    observation_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    product_name VARCHAR(512) NOT NULL,
    repeat_customer_index INT NOT NULL,
    old_shop_index INT NOT NULL,
    product_name_length INT NOT NULL,
    location_tag TINYINT NOT NULL,
    product_price DECIMAL(10,2) NOT NULL,
    payment_count BIGINT NOT NULL,
    rating_tag TINYINT NOT NULL,
    payment_is_lower_bound BOOLEAN NOT NULL,
    occurrence_count INT NOT NULL,
    first_source_row INT NOT NULL,
    PRIMARY KEY (dataset_sha256, observation_hash),
    CONSTRAINT fk_batch FOREIGN KEY (dataset_sha256) REFERENCES dataset_batch(dataset_sha256),
    CONSTRAINT chk_price CHECK (product_price > 0),
    CONSTRAINT chk_payment CHECK (payment_count >= 0),
    CONSTRAINT chk_location CHECK (location_tag BETWEEN 1 AND 5),
    CONSTRAINT chk_rating CHECK (rating_tag IN (0,1)),
    CONSTRAINT chk_occurrence CHECK (occurrence_count >= 1),
    CONSTRAINT chk_repeat_index CHECK (repeat_customer_index >= 0),
    CONSTRAINT chk_old_index CHECK (old_shop_index >= 0),
    INDEX idx_keyword_price (keyword, product_price),
    INDEX idx_payment_count (payment_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

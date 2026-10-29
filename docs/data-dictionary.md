# 字段与统计口径

数据粒度是一条商品页面相关观察；没有可靠产品 ID、统一采集时间或订单标识。`observation_hash` 是九字段内容指纹，不是平台商品 ID。

| 字段 | 含义与处理规则 |
| --- | --- |
| keyword | 来源搜索关键词，保留文本；不是标准类目编码 |
| product_name | 原商品标题；仅去首尾空白，不批量删除符号或营销文字 |
| repeat_customer_index | 保留已有“回头客指数”；不能当作复购率，源工作簿范围为 0–3000 |
| old_shop_index | 保留已有“老店指数”，范围 0–21；0 的业务含义未完全核实 |
| product_name_length | Python `len(title)`，包含数字、符号和空格；范围 3–81，与提供的字数表一致 |
| location_tag | 保留历史 1–5 编码；不将该编码作为已验证的经济发展评级 |
| product_price | 商品标价，去货币符号并用 Decimal 保留两位小数；MySQL 使用 DECIMAL(10,2) |
| payment_count | 解析页面展示付款人数，如 `1.2万+人付款` → 12000；不是订单数 |
| rating_tag | 保留历史 0/1 标签；缺少评价原文与完整定义，不解释为好评率 |
| payment_is_lower_bound | 来源含 `+` 时为 1；多条相同九特征记录合并时，只要有一条含 `+` 就保留 1 |
| occurrence_count | 相同九特征在本次来源文件中出现的次数，合计还原有效来源记录数 |
| first_source_row | 第一条对应来源工作簿数据的行号，用于本地对照 |
| dataset_sha256 | 输入标准化来源 CSV 的 SHA256，用于批次区分 |

## 去重与计数

去重键为 keyword、product_name、repeat_customer_index、old_shop_index、product_name_length、location_tag、product_price、payment_count、rating_tag。九字段完全相同时合并为一条，并保留出现次数。

这一规则用于消除相同特征的冗余观察，不能保证合并的是同一真实商品。同标题的不同商家可能被合并；同一商品在不同关键词或价格下仍可能保留多条。对于下一批完整采集，应优先采用平台商品 ID 和采集时间识别快照。

`reports/analysis/summary.json` 同时报告来源观察口径和去重特征口径。例如，来源标价中位数为 32.10 元，去重特征口径为 32.00 元；两者使用不同权重，不能混用。

## 付款人数与分析范围

21,833 条来源付款人数含有 `+`。这些值作为展示下界保留；没有 `+` 也不能保证是精确或同时段统计。所有汇总字段明确使用 `displayed_payment_count_sum`，不命名为真实销量、总用户或 GMV。

标价、标签与展示计数来自商品页面，不支持用户年龄画像、真实复购率、购买篮关联规则或因果推断。当前代码只复现描述统计、价格区间、关键词汇总和探索性 Pearson 相关。

"""Descriptive statistics; observations are not orders or identified buyers."""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import math
from pathlib import Path
import statistics

from ecommerce.pipeline import write_csv, save_json


def pearson(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    denom = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / denom if denom else None


def summarize(rows):
    prices = [float(r["product_price"]) for r in rows]
    payments = [int(r["payment_count"]) for r in rows]
    return {"feature_records": len(rows), "keyword_count": len({r["keyword"] for r in rows}),
        "title_count": len({r["product_name"] for r in rows}),
        "price_min": min(prices) if prices else None, "price_max": max(prices) if prices else None,
        "price_mean": statistics.mean(prices) if prices else None,
        "price_median": statistics.median(prices) if prices else None,
        "displayed_payment_count_sum": sum(payments),
        "displayed_payment_count_median": statistics.median(payments) if payments else None,
        "price_payment_pearson": pearson(prices,payments),
        "rating_tag_1_count": sum(int(r["rating_tag"]) for r in rows)}


def analyze(input_file, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with Path(input_file).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expanded = [r for r in rows for _ in range(int(r["occurrence_count"]))]
    summary = {"source_observations": summarize(expanded), "deduplicated_features": summarize(rows),
               "units": {"price": "CNY", "payment_count": "platform display count, sometimes a lower bound"}}
    save_json(output_dir / "summary.json", summary)
    groups = defaultdict(list)
    for row in rows:
        groups[row["keyword"]].append(row)
    keyword_stats = [{"keyword": key, "feature_records": len(group),
        "price_mean": round(statistics.mean(float(r["product_price"]) for r in group), 4),
        "price_median": statistics.median(float(r["product_price"]) for r in group),
        "displayed_payment_count_sum": sum(int(r["payment_count"]) for r in group)}
        for key, group in sorted(groups.items(), key=lambda kv:(-len(kv[1]),kv[0]))]
    write_csv(output_dir / "keyword_summary.csv", list(keyword_stats[0]) if keyword_stats else
        ["keyword","feature_records","price_mean","price_median","displayed_payment_count_sum"], keyword_stats)
    bands = Counter()
    for row in rows:
        value=Decimal(row["product_price"])
        label=next((label for limit,label in [(50,"[0,50)"),(100,"[50,100)"),(200,"[100,200)"),
                     (500,"[200,500)")] if value < limit),"[500,+inf)")
        bands[label] += 1
    write_csv(output_dir / "price_bands.csv", ["price_band","feature_records"],
        [{"price_band":label,"feature_records":bands[label]} for label in
        ["[0,50)","[50,100)","[100,200)","[200,500)","[500,+inf)"]])
    fields=["repeat_customer_index","old_shop_index","product_name_length","product_price","payment_count"]
    correlations=[{"feature_x":a,"feature_y":b,
        "pearson_r":pearson([float(r[a]) for r in rows],[float(r[b]) for r in rows])}
        for a in fields for b in fields]
    write_csv(output_dir / "correlations.csv", ["feature_x","feature_y","pearson_r"],correlations)
    return summary


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",default="reports/run/products.csv")
    parser.add_argument("--output",default="artifacts/analysis")
    args=parser.parse_args()
    analyze(args.input,args.output)

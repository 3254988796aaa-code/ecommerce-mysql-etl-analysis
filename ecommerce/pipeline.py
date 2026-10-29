"""Offline, deterministic CSV cleaning and nine-feature exact deduplication."""
import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

from ecommerce.cleaning import FEATURES, clean_record

OUTPUT_FIELDS = ["observation_hash", *FEATURES, "payment_is_lower_bound", "occurrence_count", "first_source_row"]


def write_csv(path, fields, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")


def prepare(input_file, output_dir):
    input_file, output_dir = Path(input_file).resolve(), Path(output_dir).resolve()
    if input_file.parent == output_dir or output_dir in input_file.parents:
        raise ValueError("output_must_not_contain_input")
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped, rejected = {}, []
    reference_mismatches = Counter()
    valid_count = input_count = lower_bound_count = 0
    with input_file.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"keyword", "product_name", "price_raw", "payment_raw", "repeat_customer_index",
                    "old_shop_index", "location_tag", "rating_tag"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("missing_input_columns")
        for line, raw in enumerate(reader, 2):
            input_count += 1
            try:
                row = clean_record(raw)
            except ValueError as exc:
                rejected.append({"csv_line": line, "reason": str(exc)})
                continue
            valid_count += 1
            lower_bound_count += row["payment_is_lower_bound"]
            for ref, key in (("title_length_reference", "product_name_length"),
                             ("payment_count_reference", "payment_count")):
                if raw.get(ref, "") != "" and str(row[key]) != str(raw[ref]):
                    reference_mismatches[key] += 1
            payload = json.dumps([row[k] for k in FEATURES], ensure_ascii=False, separators=(",", ":"))
            fingerprint = sha256(payload.encode("utf-8")).hexdigest()
            if fingerprint in grouped:
                existing = grouped[fingerprint]
                existing["occurrence_count"] += 1
                existing["payment_is_lower_bound"] |= row["payment_is_lower_bound"]
            else:
                grouped[fingerprint] = {"observation_hash": fingerprint, **row,
                    "occurrence_count": 1, "first_source_row": str(raw.get("source_row", line))}
    products = list(grouped.values())
    write_csv(output_dir / "products.csv", OUTPUT_FIELDS, products)
    write_csv(output_dir / "rejected.csv", ["csv_line", "reason"], rejected)
    report = {
        "pipeline_version": 1, "dataset_sha256": sha256(input_file.read_bytes()).hexdigest(),
        "input_observations": input_count, "valid_observations": valid_count,
        "rejected_observations": len(rejected), "unique_feature_records": len(products),
        "redundant_feature_rows": valid_count - len(products),
        "payment_lower_bound_source_rows": lower_bound_count,
        "rejection_reasons": dict(sorted(Counter(x["reason"] for x in rejected).items())),
        "reference_mismatches": dict(reference_mismatches),
        "dedup_key": FEATURES,
        "output_sha256": sha256((output_dir / "products.csv").read_bytes()).hexdigest(),
    }
    save_json(output_dir / "quality_report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/source/observations.csv")
    parser.add_argument("--output", default="artifacts/run")
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

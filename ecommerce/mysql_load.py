"""Transactional, parameterized and idempotent ingestion into MySQL 8.0.16+."""
import argparse
import csv
import json
import os
from pathlib import Path

from ecommerce.pipeline import OUTPUT_FIELDS

ROOT=Path(__file__).resolve().parents[1]


def create_schema(connection):
    sql=(ROOT/"sql/schema.sql").read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        for statement in sql.split(";"):
            if statement.strip():
                cursor.execute(statement)


def load_batch(connection, products_file, report_file):
    report=json.loads(Path(report_file).read_text(encoding="utf-8"))
    from hashlib import sha256
    if sha256(Path(products_file).read_bytes()).hexdigest()!=report["output_sha256"]:
        raise ValueError("products_report_hash_mismatch")
    dataset=report["dataset_sha256"]
    with Path(products_file).open(encoding="utf-8",newline="") as stream:
        records=list(csv.DictReader(stream))
    if len(records)!=report["unique_feature_records"]:
        raise ValueError("record_count_mismatch")
    if sum(int(row["occurrence_count"]) for row in records)!=report["valid_observations"]:
        raise ValueError("occurrence_count_mismatch")
    fields=["dataset_sha256",*OUTPUT_FIELDS]
    values=[tuple([dataset,*[row[k] for k in OUTPUT_FIELDS]]) for row in records]
    placeholders=",".join(["%s"]*len(fields))
    # Re-import replaces stored counts, rather than incrementing them.
    updates=",".join(f"{key}=VALUES({key})" for key in OUTPUT_FIELDS if key!="observation_hash")
    try:
        connection.begin()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO dataset_batch (dataset_sha256,input_observations,valid_observations,feature_records) "
                "VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE dataset_sha256=VALUES(dataset_sha256)",
                (dataset,report["input_observations"],report["valid_observations"],len(records)))
            query=f"INSERT INTO product_observation ({','.join(fields)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
            for start in range(0,len(values),1000):
                cursor.executemany(query,values[start:start+1000])
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {"dataset_sha256":dataset,"feature_records":len(records)}


def main():
    from dotenv import load_dotenv
    import pymysql
    load_dotenv(ROOT/".env")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",default="reports/run/products.csv")
    parser.add_argument("--report",default="reports/run/quality_report.json")
    args=parser.parse_args()
    with pymysql.connect(host=os.getenv("MYSQL_HOST","127.0.0.1"),port=int(os.getenv("MYSQL_PORT","3306")),
        user=os.getenv("MYSQL_USER","ecommerce_app"),password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE","ecommerce_portfolio"),charset="utf8mb4",connect_timeout=10) as connection:
        create_schema(connection)
        print(json.dumps(load_batch(connection,args.input,args.report),ensure_ascii=False))


if __name__=="__main__":
    main()

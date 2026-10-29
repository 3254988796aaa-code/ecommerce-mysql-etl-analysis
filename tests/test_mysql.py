import json
import os
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not os.getenv("MYSQL_TEST_PORT"),reason="Set MYSQL_TEST_PORT to run a dedicated MySQL integration database")
def test_mysql_full_load_idempotence_and_queries(tmp_path):
    import pymysql
    from ecommerce.pipeline import prepare,save_json
    from ecommerce.mysql_load import create_schema,load_batch
    prepare(ROOT/"data/source/observations.csv",tmp_path/"out")
    with pymysql.connect(host=os.getenv("MYSQL_TEST_HOST","127.0.0.1"),port=int(os.environ["MYSQL_TEST_PORT"]),
        user=os.getenv("MYSQL_TEST_USER","root"),password=os.getenv("MYSQL_TEST_PASSWORD",""),
        database=os.getenv("MYSQL_TEST_DATABASE","ecommerce_test"),charset="utf8mb4") as connection:
        create_schema(connection)
        products=tmp_path/"out/products.csv";report=tmp_path/"out/quality_report.json"
        first=load_batch(connection,products,report)
        second=load_batch(connection,products,report)
        assert first==second
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*),SUM(occurrence_count),COUNT(DISTINCT keyword) FROM product_observation WHERE dataset_sha256=%s",(first["dataset_sha256"],))
            assert tuple(map(int,cursor.fetchone()))==(28273,28722,572)
            cursor.execute("SELECT VERSION()")
            version=cursor.fetchone()[0]
            sql_text=(ROOT/"sql/analysis.sql").read_text(encoding="utf-8")
            queries="\n".join(line for line in sql_text.splitlines() if not line.lstrip().startswith("--")).split(";")
            result_counts=[]
            for query in queries:
                if query.strip():
                    cursor.execute(query)
                    result_counts.append(len(cursor.fetchall()))
        if os.getenv("MYSQL_VERIFICATION_OUTPUT"):
            save_json(os.environ["MYSQL_VERIFICATION_OUTPUT"],{
                "mysql_version":version,"dataset_sha256":first["dataset_sha256"],
                "feature_records":28273,"represented_source_observations":28722,"keywords":572,
                "same_batch_loaded_twice":True,"all_analysis_statements_executed":True,
                "analysis_statement_result_counts":result_counts})
        products.write_text(products.read_text(encoding="utf-8")+"\n",encoding="utf-8")
        with pytest.raises(ValueError,match="hash_mismatch"):load_batch(connection,products,report)

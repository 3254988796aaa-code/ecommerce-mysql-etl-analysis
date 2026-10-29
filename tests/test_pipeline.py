import csv
from pathlib import Path
import pytest
from ecommerce.pipeline import prepare,write_csv
from ecommerce.analysis import analyze

ROOT=Path(__file__).resolve().parents[1]


def sample():
    return {"source_row":2,"keyword":"demo","product_name":"测试商品","price_raw":"¥10.50",
        "payment_raw":"1.2万+人付款","repeat_customer_index":3,"old_shop_index":2,"location_tag":1,"rating_tag":0,
        "title_length_reference":4,"payment_count_reference":12000}


def test_duplicates_errors_and_reproducibility(tmp_path):
    raw=sample();path=tmp_path/"input.csv"
    write_csv(path,list(raw),[raw,{**raw,"source_row":3},{**raw,"source_row":4,"price_raw":"bad"}])
    a=prepare(path,tmp_path/"a");b=prepare(path,tmp_path/"b")
    assert a==b
    assert a["unique_feature_records"]==1 and a["redundant_feature_rows"]==1
    assert a["rejection_reasons"]=={"invalid_price":1}
    assert a["reference_mismatches"]=={}
    rows=list(csv.DictReader((tmp_path/"a/products.csv").open(encoding="utf-8")))
    assert rows[0]["occurrence_count"]=="2"
    result=analyze(tmp_path/"a/products.csv",tmp_path/"analysis")
    assert result["source_observations"]["feature_records"]==2
    assert result["deduplicated_features"]["feature_records"]==1


def test_actual_exported_data_reconciles(tmp_path):
    report=prepare(ROOT/"data/source/observations.csv",tmp_path/"out")
    assert report["input_observations"]==28722
    assert report["valid_observations"]==28722
    assert report["unique_feature_records"]==28273
    assert report["redundant_feature_rows"]==449
    assert report["reference_mismatches"]=={}
    summary=analyze(tmp_path/"out/products.csv",tmp_path/"analysis")
    assert summary["source_observations"]["keyword_count"]==572
    assert summary["source_observations"]["price_median"]==32.1


def test_invalid_headers_and_reference_mismatch(tmp_path):
    raw=sample();raw["title_length_reference"]=99
    path=tmp_path/"input.csv";write_csv(path,list(raw),[raw])
    assert prepare(path,tmp_path/"out")["reference_mismatches"]=={"product_name_length":1}
    path.write_text("wrong\nvalue\n",encoding="utf-8")
    with pytest.raises(ValueError,match="missing_input_columns"):prepare(path,tmp_path/"out")

"""Export supplied workbook stages into a reproducible CSV; never edits Excel."""
import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ecommerce.cleaning import FEATURES, clean_record
from ecommerce.pipeline import save_json, write_csv

NAMES=["最终版(1).xlsx","清洗后_付款人数已转换_新增评价标签.xlsx",
       "0_processed_新增指数列.xlsx","产品名称的字数.xlsx","编码后的数据.xlsx"]


def load_sheet(path):
    from openpyxl import load_workbook
    workbook=load_workbook(path,read_only=True,data_only=True)
    try:
        return list(workbook.worksheets[0].values)
    finally:
        workbook.close()


def export(source_dir,output_dir):
    source_dir,output_dir=Path(source_dir),Path(output_dir)
    sheets={name:load_sheet(source_dir/name) for name in NAMES}
    final,middle,indices,lengths,encoded=[sheets[name][1:] for name in NAMES]
    if len({len(x) for x in (final,middle,indices,lengths,encoded)})!=1:
        raise ValueError("workbook_row_count_mismatch")
    records=[]
    mismatches=Counter()
    for position,(f,m,i,l,e) in enumerate(zip(final,middle,indices,lengths,encoded),2):
        if not f[1]==m[3]==l[0]==e[3]:
            raise ValueError(f"title_alignment_mismatch_at_row_{position}")
        record={"source_row":position,"keyword":m[0],"product_name":m[3],
                "shop_display":m[1],"shop_badge":i[0],"location_text":m[2],
                "price_raw":e[4],"payment_raw":m[4],
                "repeat_customer_index":i[2],"old_shop_index":i[3],
                "location_tag":e[14],"rating_tag":m[12],
                "title_length_reference":l[1],"payment_count_reference":m[11]}
        cleaned=clean_record(record)
        for key,expected in zip(FEATURES,f):
            actual=cleaned[key]
            if key=="product_price":
                from decimal import Decimal
                match=Decimal(str(expected))==Decimal(actual)
            else:
                match=actual==expected
            if not match:
                mismatches[key]+=1
        records.append(record)
    output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(output_dir/"observations.csv",list(records[0]),records)
    audit={"workbooks":[{"file":name,"sha256":sha256((source_dir/name).read_bytes()).hexdigest(),
        "first_sheet_records":len(sheets[name])-1} for name in NAMES],
        "exported_records":len(records),"final_feature_comparison_mismatches":dict(mismatches),
        "reference_exact_duplicate_rows":len(final)-len(set(final)),
        "title_alignment_checked_records":len(records),
        "index_alignment_note":"Index-only workbook has no product identifier; row order follows supplied stages and is checked against final features.",
        "collection_method":"Octoparse, confirmed by project author", "platform":"Taobao, as described in the reference report",
        "collection_timestamp":"not available in supplied final-stage workbooks"}
    save_json(output_dir/"source_manifest.json",audit)
    return audit


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir",required=True)
    parser.add_argument("--output",default="data/source")
    args=parser.parse_args()
    print(export(args.source_dir,args.output))

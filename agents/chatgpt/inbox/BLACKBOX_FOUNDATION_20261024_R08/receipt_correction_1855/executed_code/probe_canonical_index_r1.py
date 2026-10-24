"""Read-only, one-file schema compatibility probe; no publication or PIT claim."""
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from r06_bundle_store import digest
from canonical_index_schema_r1 import normalize_canonical_index

SOURCE=Path(r'E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions\INDEX_DAILY_RAW_FULL_HISTORY_R1\REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123\RAW_FILES\index_daily__399303_XSHE__to_20260804.parquet')
SHA='1c5b5d2b3d89c9001e23f5c221f27e2d27104fd27b77d78187abc5e85352f200'


def main():
    if digest(SOURCE)!=SHA:
        raise ValueError('SOURCE_SHA_CHANGED')
    original=pq.ParquetFile(SOURCE).read().to_pandas()
    mapped=normalize_canonical_index(original)
    if len(original)!=len(mapped) or len(mapped)!=5242 or mapped['close'].notna().sum()!=3004:
        raise ValueError('R08_SOURCE_COUNTS_CHANGED')
    pd.testing.assert_series_equal(original['close'],mapped['close'])
    pd.testing.assert_series_equal(original['amount'],mapped['money'],check_names=False)
    pd.testing.assert_series_equal(original['canonical_code'],mapped['code'],check_names=False)
    missing=set(original.columns)-{'canonical_code','trade_date','amount'}-set(mapped.columns)
    if missing or 'known_at' in mapped or 'pit_status' in mapped:
        raise ValueError('UNAUTHORIZED_METADATA_CHANGE')
    valued=mapped[mapped['close'].notna()]
    h1=valued[valued['date'].between('2026-01-05','2026-07-29')]
    if digest(SOURCE)!=SHA:
        raise ValueError('SOURCE_CHANGED_DURING_PROBE')
    print(json.dumps({'status':'SCHEMA_ADAPTER_PROBE_PASS','source':str(SOURCE),'source_sha256':SHA,
                      'input_rows':len(original),'output_rows':len(mapped),'valued_closes':len(valued),
                      'valued_min':str(valued['date'].min()),'valued_max':str(valued['date'].max()),
                      'h1_2026_distinct_valued_dates':int(h1['date'].nunique()),
                      'source_columns':list(original.columns),'normalized_columns':list(mapped.columns),
                      'raw_to_formal_or_engine_admission':False,'source_loss_inferred':False,
                      'DATA_WRITES':0,'NETWORK_CALLS':0},ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()

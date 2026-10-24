"""R10 read-only schema examination helper (inspection only, no writes to inspected files).

Reads exact paths, verifies SHA256 pins, records Arrow/physical schema, pandas metadata index_columns,
in-memory index, and date-like value observations. Never parses integer axes as dates, never fills
factors, never renames or resets indexes, never persists modified frames.
"""
import datetime as _dt
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

DATE_NAME = re.compile(r'(?i)(date|time|dt|day|timestamp|asof|trade_date|index)')
DATE_TYPES = (pa.date32(), pa.date64())
TS_TYPE = pa.types.is_timestamp
TIME_TYPE = pa.types.is_time


def sha(b):
    return hashlib.sha256(b).hexdigest()


def non_null_distinct(series):
    return int(series.dropna().nunique())


def lit(v):
    """Literal representation, no conversion, no timezone normalization."""
    if v is None:
        return None
    if hasattr(v, 'item') and not isinstance(v, (str, bytes)):
        try:
            v = v.item()
        except Exception:
            return repr(v)
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)):
        return v
    if isinstance(v, (_dt.date, _dt.datetime, _dt.time)):
        return v.isoformat()
    return repr(v)


def series_stats(s, tail=5):
    vals = s.tolist()
    import pandas as pd
    st = {
        'dtype': str(s.dtype),
        'null_count': int(s.isna().sum()),
        'non_null_count': int(s.notna().sum()),
        'distinct_non_null': non_null_distinct(s),
        'first_five_literals': [lit(x) for x in vals[:5]],
        'last_five_literals': [lit(x) for x in vals[-tail:]],
    }
    if pd.api.types.is_numeric_dtype(s) and s.notna().any():
        st['observed_min_literal'] = lit(s.min())
        st['observed_max_literal'] = lit(s.max())
        st['observed_min_max_are_dates'] = False
    return st


def arrow_field_type(t):
    return str(t)


def is_date_like_arrow(t):
    if t in DATE_TYPES:
        return True
    if TS_TYPE(t) or TIME_TYPE(t):
        return True
    return False


def explicit_calendar_dates(s):
    """Only for genuine Arrow date/timestamp columns. Returns sorted set of ISO dates or None."""
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(s):
        v = s.dropna()
        return sorted({x.date().isoformat() for x in v})
    return None


def examine(path, expected_sha):
    path = Path(path)
    rec = {'path': str(path), 'exists': path.exists()}
    if not path.exists():
        rec['stopped'] = 'FILE_NOT_PRESENT'
        return rec
    b = path.read_bytes()
    rec['bytes'] = len(b)
    rec['sha256'] = sha(b)
    rec['pinned_sha256'] = expected_sha
    rec['pin_match'] = (expected_sha is None) or (rec['sha256'] == expected_sha)
    if not rec['pin_match']:
        rec['stopped'] = 'PIN_CHANGED'
        return rec

    pf = pq.ParquetFile(io.BytesIO(b))
    md = pf.metadata
    arrow_schema = pf.schema_arrow
    rec['row_count'] = int(md.num_rows)
    rec['num_columns'] = int(md.num_columns)
    rec['num_row_groups'] = int(md.num_row_groups)
    rec['created_by'] = md.created_by
    rec['arrow_schema'] = [{'name': f.name, 'arrow_type': arrow_field_type(f.type),
                            'nullable': bool(f.nullable),
                            'metadata': ({k.decode('utf-8', 'replace'):
                                          v.decode('utf-8', 'replace') for k, v in (f.metadata or {}).items()}
                                         if f.metadata else {})}
                           for f in arrow_schema]

    kv = md.metadata or {}
    pandas_raw = kv.get(b'pandas')
    pandas_meta = None
    if pandas_raw:
        try:
            pandas_meta = json.loads(pandas_raw.decode('utf-8'))
        except Exception:
            pandas_meta = {'undecodable': True}
    rec['parquet_key_value_metadata_keys'] = sorted(k.decode('utf-8', 'replace') for k in kv)
    rec['pandas_metadata'] = {
        'index_columns': pandas_meta.get('index_columns'),
        'column_indexes': pandas_meta.get('column_indexes'),
        'pandas_version': pandas_meta.get('pandas_version'),
        'creator': (pandas_meta.get('creator') or {}).get('library') if isinstance(pandas_meta.get('creator'), dict) else pandas_meta.get('creator'),
        'columns_count': len(pandas_meta.get('columns') or []),
    } if pandas_meta else None

    table = pq.read_table(io.BytesIO(b))
    df = table.to_pandas()          # in-memory view only; never persisted
    idx = df.index
    rec['in_memory_index'] = {
        'name': idx.name if not isinstance(idx, __import__('pandas').MultiIndex) else list(idx.names),
        'nlevels': int(getattr(idx, 'nlevels', 1)),
        'dtype': str(idx.dtype),
        'length': int(len(idx)),
    }

    cols = list(df.columns)
    rec['physical_column_order'] = cols
    rec['date_like_fields'] = {}
    for c in cols:
        f = arrow_schema.field(c)
        if DATE_NAME.search(str(c)) or is_date_like_arrow(f.type):
            st = series_stats(df[c])
            st['arrow_type'] = arrow_field_type(f.type)
            st['identified_by'] = ('name' if DATE_NAME.search(str(c)) else '') + \
                                   ('+type' if is_date_like_arrow(f.type) else '')
            if is_date_like_arrow(f.type):
                cal = explicit_calendar_dates(df[c])
                if cal is not None:
                    st['observed_calendar_dates_count'] = len(cal)
                    st['observed_calendar_min'] = cal[0] if cal else None
                    st['observed_calendar_max'] = cal[-1] if cal else None
                    st['explicit_daily_axis'] = True
                    st['dates_after_20260814'] = [d for d in cal if d > '2026-08-14']
                else:
                    st['explicit_daily_axis'] = False
            else:
                st['explicit_daily_axis'] = False
                st['integer_or_non_date_axis_uninterpreted'] = True
            rec['date_like_fields'][str(c)] = st

    if getattr(idx, 'nlevels', 1) > 1:
        rec['index_level_stats'] = {}
        for i, nm in enumerate(idx.names):
            ser = __import__('pandas').Series(idx.get_level_values(i))
            rec['index_level_stats'][str(nm)] = series_stats(ser)
    else:
        ser = __import__('pandas').Series(idx)
        rec['index_level_stats'] = {str(idx.name): series_stats(ser)}

    head_cols = [c for c in ('date', 'time', 'datetime', 'code', 'factor') if c in cols]
    rec['head_samples'] = {'columns': head_cols,
                           'rows': [{c: lit(df[c].iloc[i]) for c in head_cols}
                                    for i in range(min(5, len(df)))]}
    rec['dtypes'] = {c: str(df[c].dtype) for c in cols}
    rec['total_null_cells'] = int(df.isna().sum().sum())
    return rec


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    out = {'schema': 'R10_READ_ONLY_SCHEMA_EXAMINATION_1',
           'mode': 'OBSERVATION_ONLY_NOT_SCHEMA_ADMISSION',
           'rules': ['no integer date parsed as nanoseconds',
                     'no alternate time field substituted',
                     'no date inferred from filename',
                     'no timezone normalization',
                     'no factor filled',
                     'no frame modified or persisted'],
           'targets': []}
    for t in spec['targets']:
        out['targets'].append(examine(t['path'], t.get('sha256')))
    Path(spec['out']).write_bytes((json.dumps(out, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))
    for t in out['targets']:
        print(t.get('path'), '|rows', t.get('row_count'), '|cols', t.get('num_columns'),
              '|date_like', list(t.get('date_like_fields') or {}),
              '|pin', t.get('pin_match'), t.get('stopped', ''))


if __name__ == '__main__':
    main()

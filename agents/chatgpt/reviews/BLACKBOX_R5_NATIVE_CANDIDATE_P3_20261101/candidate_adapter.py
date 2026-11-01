"""BLACKBOX P3 value-preserving candidate adapter. Bounded native entry separately gated.

No network, supplier, production imports, CURRENT selection or release operations.
Only physical-row admission and exact value-preserving projections are implemented.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

FIELDS = ['time', 'code', 'open', 'high', 'low', 'close', 'volume',
          'money', 'paused', 'high_limit', 'low_limit', 'avg', 'pre_close', 'factor']
NUMERIC = FIELDS[2:]
EXPECTED = pa.schema([pa.field('time', pa.timestamp('ns')),
                      pa.field('code', pa.string())] +
                     [pa.field(n, pa.float64()) for n in NUMERIC])
FAMILIES = {'stock': 'price/stock_ohlcv_daily', 'etf': 'price/ETF_daily',
            'index': 'reference/index_daily'}
PIT = 'NOT_ESTABLISHED'
USES = ['OFFLINE_VALUE_AUDIT', 'SCHEMA_INSPECTION']


class Blocked(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise Blocked(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packed(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def load_pinned(path, identity):
    return json.loads(verify_identity(path, identity))


def verify_identity(path, identity):
    data = read_regular(path)
    require(len(data) == identity['bytes'] and sha(data) == identity['sha256'],
            'INPUT_IDENTITY:' + str(path))
    return data


def read_regular(path):
    path = Path(path)
    require(path.is_file() and not any(p.is_symlink() for p in [path, *path.parents]),
            'SOURCE_SYMLINK_OR_NOT_REGULAR')
    for part in [path,*path.parents]:
        if getattr(part.lstat(), 'st_file_attributes', 0) & 0x400:
            raise Blocked('REPARSE_POINT')
    return path.read_bytes()


def relative(value):
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and
            str(p) == value and '\\' not in value and ':' not in value,
            'UNSAFE_RELATIVE_PATH')
    return value


def source_key(entry, bindings):
    path = entry['source']['path']
    matches = [(name, prefix) for name, prefix in bindings['source_prefixes'].items()
               if path.startswith(prefix)]
    require(len(matches) == 1, 'SOURCE_ROOT_NOT_BOUND')
    name, prefix = matches[0]
    rel = relative(PureWindowsPath(path[len(prefix):]).as_posix())
    return name, rel


def check_positions(admitted, quarantine, count):
    require(all(type(x) is int for x in admitted + quarantine), 'POSITION_NOT_INT')
    require(len(set(admitted)) == len(admitted) and
            len(set(quarantine)) == len(quarantine), 'REPEATED_POSITION')
    a, q = set(admitted), set(quarantine)
    require(not a & q and a | q == set(range(count)), 'POSITION_PARTITION')


def decode(data, entry):
    require(len(data) == entry['source']['bytes'] and
            sha(data) == entry['source']['sha256'], 'SOURCE_IDENTITY')
    pf = pq.ParquetFile(io.BytesIO(data))
    physical = pf.read()
    require(physical.column_names == FIELDS + ['__index_level_0__'], 'RAW_COLUMNS')
    require(physical.select(FIELDS).schema.remove_metadata() == EXPECTED, 'RAW_ARROW_SCHEMA')
    require(physical.schema.field('__index_level_0__').type == pa.int64(), 'INDEX_SCHEMA')
    # Physical order defines admission; the saved pandas index never selects rows.
    indices = physical['__index_level_0__'].to_pylist()
    require(indices == list(range(physical.num_rows)), 'INDEX_POSITION_MISMATCH_REVIEW_REQUIRED')
    frame = physical.to_pandas()
    require(list(frame.columns) == FIELDS and frame.index.tolist() == indices, 'PANDAS_RESTORE')
    require(str(frame.time.dtype) == 'datetime64[ns]' and str(frame.code.dtype) == 'str',
            'PANDAS_TYPES')
    require(all(str(frame[n].dtype) == 'float64' for n in NUMERIC), 'NUMERIC_TYPES')
    check_positions(entry['admitted_positions'], entry['quarantined_positions'], len(frame))
    require(not frame.time.isna().any() and not frame.code.isna().any(), 'NULL_KEY')
    require(all(type(x) is str and re.fullmatch(r'\d{6}\.(XSHG|XSHE)', x)
                for x in frame.code), 'JQ_CODE_NAMESPACE')
    require((frame.time == pd.Timestamp(entry['date'])).all(), 'EXACT_DATE_OR_TIME')
    require(not np.isinf(frame[NUMERIC].to_numpy()).any(), 'NONFINITE_VALUE')
    require(set(frame.paused.unique()) <= {0.0, 1.0}, 'UNKNOWN_PAUSED_STATE')
    admitted = frame.iloc[entry['admitted_positions']]
    require(not admitted[NUMERIC].isna().any().any(), 'ADMITTED_NULL')
    q = entry['quarantined_positions']
    if q:
        require(q == [7] and len(frame) == 80 and entry['product'] == 'stock'
                and entry['date'] == '2026-10-27'
                and entry['source']['bytes'] == 15489
                and entry['source']['sha256'] ==
                'fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7'
                and entry['source']['path'].endswith('\\raw\\stock\\2026-10-27_03360_R4.parquet'),
                'QUARANTINE_EXACT_BINDING')
        row = frame.iloc[7]
        require(row.code == '600621.XSHG' and row[['open', 'high', 'low']].isna().all()
                and row.paused == row.volume == row.money == 0
                and row.close == row.avg == row.pre_close == 14.9
                and row.high_limit == 16.39 and row.low_limit == 13.41
                and row.factor == 1.0, 'QUARANTINE_VALUES')
    audit = {'rows': len(frame), 'footer_schema': str(pf.schema).split('\n', 1)[1],
             'arrow_schema': str(physical.schema.remove_metadata()),
             'arrow_metadata_sha256': sha(packed({k.decode(): v.decode()
                for k, v in (physical.schema.metadata or {}).items()})),
             'pandas_dtypes': frame.dtypes.astype(str).to_dict(),
             'saved_index_matches_physical_position': True,
             'index_used_for_admission': False}
    return physical.select(FIELDS).replace_schema_metadata(None), audit


class BodyReader:
    """Exact handoff bodies only. No directory scan or alternative source fallback."""
    def __init__(self, root, bindings):
        self.root = Path(root)
        self.plan = load_pinned(self.root / 'RAW_TRANSFER_PLAN.json', bindings['plan'])
        self.manifest = load_pinned(self.root / 'RAW_BODY_MANIFEST.json', bindings['handoff'])
        self.admission = load_pinned(self.root / 'ADMISSION_R5.json', bindings['admission'])
        reuse = load_pinned(self.root / 'REUSE_MANIFEST_R5.json', bindings['reuse_manifest'])
        cells = [[product, date] for product, days in reuse['r1']['plan']['increment_days'].items()
                 for date in days]
        require(cells == bindings['expected_cells'] and len(cells) == 51, 'REVIEWED_CALENDAR_BINDING')
        for name in ('pit_contract', 'domain_contract', 'original_consumer'):
            identity = bindings[name]
            verify_identity(self.root / relative(identity['name']), identity)
        require(self.admission['row_position_base'] == 0 and
                self.admission['source_values_changed'] is False, 'ADMISSION_HEADER')
        base = [{k: r[k] for k in ('root', 'relative_path', 'bytes', 'sha256', 'action')}
                for r in self.manifest['sources']]
        expected = [{k: r[k] for k in ('root', 'relative_path', 'bytes', 'sha256', 'action')}
                    for r in self.plan['rows']]
        require(base == expected, 'PLAN_HANDOFF_DIVERGENCE')
        self.rows = {(r['root'], relative(r['relative_path'])): r for r in self.manifest['sources']}
        require(len(self.rows) == len(self.plan['rows']) == 1504, 'SOURCE_COUNT_OR_DUPLICATE')
        entries = self.admission['entries']
        require(len(entries) == 1504, 'ADMISSION_COUNT')
        self.entry_keys = [source_key(e, bindings) for e in entries]
        require(len(set(self.entry_keys)) == 1504 and set(self.entry_keys) == set(self.rows),
                'ADMISSION_SOURCE_SET')
        self.archives = {}
        self.archive_identities = self.manifest['archives']
        for arc in self.archive_identities:
            relative(arc['name'])
            data = read_regular(self.root / arc['name'])
            require(len(data) == arc['bytes'] and sha(data) == arc['sha256'], 'ARCHIVE_IDENTITY')
            z = zipfile.ZipFile(io.BytesIO(data))
            members = [r['member'] for r in self.rows.values() if r.get('archive') == arc['name']]
            require(len(z.namelist()) == len(set(z.namelist())) and
                    set(z.namelist()) == set(members), 'ARCHIVE_MEMBERS')
            require(all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist()),
                    'ARCHIVE_ENCODING')
            self.archives[arc['name']] = z
        self.bindings = bindings

    def read(self, entry, key):
        r = self.rows[key]
        require(entry['source']['bytes'] == r['bytes'] and
                entry['source']['sha256'] == r['sha256'], 'PLAN_SOURCE_IDENTITY')
        require(entry['product'] == key[1].split('/')[1], 'PRODUCT_PATH')
        if r['action'] == 'CAPTURE':
            require(relative(r['member']) == r['root'] + '/' + r['relative_path'], 'MEMBER_IDENTITY')
            return self.archives[r['archive']].read(r['member'])
        require(r['action'] == 'REUSE_HUB_BODY' and key in {
                ('R1', 'raw/stock/2026-09-28_00000.parquet'),
                ('R4', 'raw/stock/2026-10-27_03360_R4.parquet')}, 'UNBOUND_REFERENCE')
        return read_regular(self.root / key[1].split('/')[-1])

    def verify_storage_again(self):
        for arc in self.archive_identities:
            b = read_regular(self.root / arc['name'])
            require(len(b) == arc['bytes'] and sha(b) == arc['sha256'], 'ARCHIVE_CHANGED')
        for entry, key in zip(self.admission['entries'], self.entry_keys):
            b = self.read(entry, key)
            require(len(b) == entry['source']['bytes'] and sha(b) == entry['source']['sha256'],
                    'SOURCE_CHANGED')


def reject_duplicates(table):
    f = table.select(['time', 'code']).to_pandas()
    require(not f.duplicated(['time', 'code']).any(), 'DUPLICATE_KEY_NO_SUPPRESSION')


def dictionary_view(table):
    """Explicit stock_daily dictionary projection, never a global rename."""
    require(table.schema.remove_metadata() == EXPECTED, 'VIEW_SCHEMA')
    names = ['trade_date' if n == 'time' else 'symbol' if n == 'code' else n for n in FIELDS]
    view = table.rename_columns(names)
    reverse = view.rename_columns(FIELDS)
    require(reverse.equals(table), 'DICTIONARY_ROUNDTRIP')
    return view


def observations(frame):
    factor = frame.factor
    paused = frame.paused.eq(1)
    equal = frame[['open', 'high', 'low', 'close']].eq(frame.pre_close, axis=0).all(axis=1)
    zero = frame.volume.eq(0) & frame.money.eq(0)
    return {'rows': len(frame), 'paused_1': int(paused.sum()),
            'paused_0': int(frame.paused.eq(0).sum()),
            'paused_1_ohlc_eq_pre_close_volume_money_zero': int((paused & equal & zero).sum()),
            'volume_money_zero': int(zero.sum()),
            'paused_0_zero_trade_price_incomplete': int((~paused & zero &
                frame[['open', 'high', 'low', 'close']].isna().any(axis=1)).sum()),
            'nulls': frame[FIELDS].isna().sum().astype(int).to_dict(),
            'factor': {'null': int(factor.isna().sum()), 'inf': int(np.isinf(factor).sum()),
                       'zero': int(factor.eq(0).sum()), 'negative': int(factor.lt(0).sum()),
                       'one': int(factor.eq(1).sum()),
                       'not_one_nonnull': int((factor.notna() & factor.ne(1)).sum()),
                       'minimum': None if factor.dropna().empty else float(factor.min()),
                       'maximum': None if factor.dropna().empty else float(factor.max())}}


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data)
    require(path.read_bytes() == data, 'JSON_OR_FILE_READBACK')


def generation_for(output, bindings):
    # The same generation cannot be moved to a new directory for a retry.
    identity = {'output_root': str(Path(output).resolve()),
                'bindings_sha256': sha(packed(bindings)),
                'implementation_sha256': sha(read_regular(__file__)),
                'package_sha256': sha(read_regular(Path(__file__).parent/'PACKAGE.json'))}
    return 'P3_R5_' + sha(packed(identity)).upper()


def parquet_new(path, table, generation):
    sink = io.BytesIO()
    t = table.replace_schema_metadata({b'candidate_generation': generation.encode(),
                                      b'historical_pit': PIT.encode(),
                                      b'supplier_namespace': b'JQ', b'price_basis': b'RAW_NONE',
                                      b'permitted_uses': packed(USES)})
    pq.write_table(t, sink, version='2.6', compression='NONE')
    write_new(path, sink.getvalue())
    got = pq.ParquetFile(path).read().replace_schema_metadata(None)
    require(got.equals(table.replace_schema_metadata(None)), 'OUTPUT_ROUNDTRIP')


def validate_output(output, source_roots):
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), 'OUTPUT_EXISTS')
    for p in [output.parent, *output.parent.parents]:
        require(not p.is_symlink() and not getattr(p.lstat(), 'st_file_attributes', 0) & 0x400,
                'OUTPUT_REPARSE')
    require(all(not (Path(r).resolve() == output.resolve() or
                     Path(r).resolve() in output.resolve().parents) for r in source_roots),
            'OUTPUT_IN_SOURCE')


def build(reader, output, generation):
    if os.name == 'nt':
        from native_reader import NativeBodyReader
        require(type(reader) is NativeBodyReader and reader.native_gate_verified, 'NATIVE_GATE_REQUIRED')
    require((pd.__version__, pa.__version__, np.__version__) == ('3.0.3', '24.0.0', '2.5.4'),
            'RUNTIME_PIN')
    require(re.fullmatch(r'[A-Z0-9_]{1,100}', generation) is not None, 'GENERATION')
    output = Path(output)
    require(generation == generation_for(output, reader.bindings), 'GENERATION_ROOT_CODE_BINDING')
    validate_output(output, getattr(reader, 'source_roots', [reader.root]))
    output.mkdir(exist_ok=False)
    try:
        return _build(reader, output, generation)
    except Exception as e:
        write_new(output / 'FAILED.json', packed({'generation': generation,
            'outcome': 'FAILED', 'error_type': type(e).__name__, 'error': str(e),
            'permitted_uses': [], 'historical_pit': PIT}))
        raise


def _build(reader, output, generation):
    buckets = defaultdict(list)
    raw_cells = defaultdict(list)
    quarantine_cells = defaultdict(list)
    sources = []
    raw_frames, admitted_frames, q_frames = [], [], []
    lineage = defaultdict(list)
    quarantine = []
    for entry, key in zip(reader.admission['entries'], reader.entry_keys):
        raw, audit = decode(reader.read(entry, key), entry)
        source_id = len(sources)
        sources.append({'source_id': source_id, 'original_path': entry['source']['path'],
                        'root': key[0], 'relative_path': key[1], **entry['source'], **audit})
        raw_frames.append(raw.to_pandas())
        a, q = entry['admitted_positions'], entry['quarantined_positions']
        admitted = raw.take(pa.array(a, pa.int64()))
        cell = entry['product'], entry['date']
        raw_cells[cell].append(raw.to_pandas())
        require(cell in [tuple(c) for c in reader.bindings['expected_cells']], 'UNBOUND_CELL')
        buckets[cell].append(admitted)
        admitted_frames.append(admitted.to_pandas())
        # Position inside each unsorted aggregate is fixed by source-plan order.
        for position in a:
            lineage[cell].append({'source_id': source_id, 'source_sha256': entry['source']['sha256'],
                                 'physical_row_position': position})
        if q:
            qr = raw.take(pa.array(q, pa.int64()))
            q_frames.append(qr.to_pandas())
            quarantine_cells[cell].append(qr.to_pandas())
            quarantine.append({'source_id': source_id, 'source_path': entry['source']['path'],
                'source_bytes': entry['source']['bytes'], 'source_sha256': entry['source']['sha256'],
                'physical_row_position': 7, 'code': '600621.XSHG', 'date': entry['date'],
                'reason': 'SUPPLIER_ZERO_TRADE_PRICE_INCOMPLETE_CANDIDATE',
                'legal_suspension_status': 'NOT_INFERRED', 'historical_pit': PIT})
            parquet_new(output / 'quarantine/original_row.parquet', qr, generation)
    require(set(buckets) == {tuple(c) for c in reader.bindings['expected_cells']}, 'CELL_COVERAGE')
    cells, products = [], Counter()
    outputs = []
    for (product, date), pieces in sorted(buckets.items()):
        table = pa.concat_tables(pieces)
        reject_duplicates(table)
        rel = 'native/' + FAMILIES[product] + '/' + date + '.parquet'
        parquet_new(output / rel, table, generation)
        outputs.append({'product': product, 'date': date, 'path': rel, 'rows': len(table)})
        if product == 'stock':
            parquet_new(output / ('dictionary/stock_daily/' + date + '.parquet'),
                        dictionary_view(table), generation)
        rows = lineage[(product, date)]
        for i, row in enumerate(rows):
            row['output_row_position'] = i
        write_new(output / ('lineage/' + product + '/' + date + '.json'), packed(rows))
        qn = sum(1 for r in quarantine if product == 'stock' and r['date'] == date)
        raw_cell = pd.concat(raw_cells[(product, date)], ignore_index=True)
        q_cell = (pd.concat(quarantine_cells[(product, date)], ignore_index=True)
                  if quarantine_cells[(product, date)] else raw_cell.iloc[:0])
        cells.append({'product': product, 'date': date, 'input': len(raw_cell),
                      'output': len(table), 'excluded': qn,
                      'facts': {'raw': observations(raw_cell),
                                'admitted': observations(table.to_pandas()),
                                'quarantined': observations(q_cell)}})
        require(len(raw_cell) == len(table) + qn == len(table) + len(q_cell), 'CELL_CONSERVATION')
        products[product] += len(table)
    raw = pd.concat(raw_frames, ignore_index=True)
    admitted = pd.concat(admitted_frames, ignore_index=True)
    excluded = pd.concat(q_frames, ignore_index=True) if q_frames else raw.iloc[:0]
    require((len(raw), len(admitted), len(excluded)) == (117461, 117460, 1), 'ROW_CONSERVATION')
    require(dict(products) == {'stock': 88811, 'etf': 28530, 'index': 119}, 'PRODUCT_COUNTS')
    require(len(quarantine) == 1, 'QUARANTINE_COUNT')
    reader.verify_storage_again()
    report = {'generation': generation, 'outcome': 'BUILT_PIT_NOT_ESTABLISHED',
              'permitted_uses': USES, 'historical_pit': PIT,
              'backtest_admission': False, 'release_admission': False,
              'original_consumer_value_projection': 'GPT_OFFLINE_SOURCE_FUNCTION_PROJECTION_ONLY_NOT_ENGINE_ADMISSION',
              'live_current_overlap': 'NOT_MERGED_WITH_CURRENT_COVERAGE_NOT_CERTIFIED',
              'native_execution': 'SCOPED_P3' if os.name == 'nt' else 'GPT_OFFLINE', 'source_files': len(sources),
              'price_basis': 'RAW_NONE', 'supplier_namespace': 'JQ',
              'implementation_sha256': sha(read_regular(__file__)),
              'conservation': {'input': len(raw), 'output': len(admitted), 'excluded': len(excluded)},
              'product_output_rows': dict(products), 'cells': cells, 'outputs': outputs,
              'facts': {'raw': observations(raw), 'admitted': observations(admitted),
                        'quarantined': observations(excluded)},
              'inputs_verified_again': True,
              'runtime': {'python': sys.version, 'pandas': pd.__version__,
                          'pyarrow': pa.__version__, 'numpy': np.__version__},
              'bindings_sha256': sha(packed(reader.bindings))}
    write_new(output / 'SOURCES.json', packed(sources))
    write_new(output / 'EXCLUSIONS.json', packed(quarantine))
    write_new(output / 'RESULT.json', packed(report))
    # Only enumerate the new candidate tree for receipts; never inventory source layers.
    expected = {'quarantine/original_row.parquet','SOURCES.json','EXCLUSIONS.json','RESULT.json'}
    for product,date in buckets:
        expected.add('native/' + FAMILIES[product] + '/' + date + '.parquet')
        expected.add('lineage/' + product + '/' + date + '.json')
        if product == 'stock':expected.add('dictionary/stock_daily/' + date + '.parquet')
    actual = {x.relative_to(output).as_posix() for x in output.rglob('*') if x.is_file()}
    require(actual == expected and len(expected) == 123, 'EXACT_EXPECTED_OUTPUT_SET')
    manifest = []
    for path in sorted(output.rglob('*')):
        if path.is_file():
            b = path.read_bytes()
            manifest.append({'path': path.relative_to(output).as_posix(),
                             'bytes': len(b), 'sha256': sha(b)})
    write_new(output / 'MANIFEST.json', packed({'generation': generation, 'files': manifest}))
    verify_candidate(output, generation)
    # A bounded build receipt, not a PIT/release/engine certificate.
    write_new(output / 'BUILD_COMPLETE.json', packed({'generation': generation,
        'outcome': 'BUILT_PIT_NOT_ESTABLISHED', 'manifest_sha256': sha((output/'MANIFEST.json').read_bytes()),
        'historical_pit': PIT, 'permitted_uses': USES, 'backtest_admission': False}))
    return report


def verify_candidate(root, generation):
    root = Path(root)
    manifest = json.loads((root / 'MANIFEST.json').read_bytes())
    require(manifest['generation'] == generation, 'GENERATION_BINDING')
    expected = set()
    for row in manifest['files']:
        rel = relative(row['path'])
        require(rel not in expected, 'MANIFEST_DUPLICATE')
        expected.add(rel)
        p = root / rel
        require(not p.is_symlink(), 'CANDIDATE_SYMLINK')
        b = p.read_bytes()
        require(len(b) == row['bytes'] and sha(b) == row['sha256'], 'CANDIDATE_IDENTITY')
        if rel.endswith('.parquet'):
            md = pq.ParquetFile(io.BytesIO(b)).schema_arrow.metadata
            require(md[b'candidate_generation'].decode() == generation and
                    md[b'historical_pit'].decode() == PIT and
                    md[b'supplier_namespace'] == b'JQ' and md[b'price_basis'] == b'RAW_NONE' and
                    json.loads(md[b'permitted_uses']) == USES, 'PARQUET_GENERATION_OR_PIT')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual - {'MANIFEST.json', 'BUILD_COMPLETE.json'} == expected, 'CANDIDATE_FILE_SET')
    complete = root / 'BUILD_COMPLETE.json'
    if complete.exists():
        c = json.loads(complete.read_bytes())
        require(c['generation'] == generation and c['outcome'] == 'BUILT_PIT_NOT_ESTABLISHED'
                and c['historical_pit'] == PIT and c['permitted_uses'] == USES
                and c['backtest_admission'] is False
                and c['manifest_sha256'] == sha((root / 'MANIFEST.json').read_bytes()),
                'BUILD_RECEIPT_BINDING')
    return manifest


def read_candidate(root, generation, product, purpose):
    require(purpose in USES, 'USE_NOT_ADMITTED_PIT_NOT_ESTABLISHED')
    require(product in FAMILIES, 'UNKNOWN_PRODUCT')
    root = Path(root)
    require((root / 'BUILD_COMPLETE.json').is_file(), 'INCOMPLETE_CANDIDATE')
    verify_candidate(root, generation)
    report = json.loads((root / 'RESULT.json').read_bytes())
    require(report['generation'] == generation and report['historical_pit'] == PIT
            and report['backtest_admission'] is False, 'RESULT_BINDING')
    paths = [root / r['path'] for r in report['outputs'] if r['product'] == product]
    table = pa.concat_tables([pq.ParquetFile(p).read().replace_schema_metadata(None) for p in paths])
    reject_duplicates(table)
    return table

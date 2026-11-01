"""Meaningful failure-injection tests, plus one complete real-body build and audit."""
from __future__ import annotations

import ast
import copy
import io
import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import candidate_adapter as c

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'evidence'
BINDINGS = json.loads((ROOT/'p3_dispatch'/'bindings.json').read_text())
ITERATION = os.environ.get('BLACKBOX_OFFLINE_TEST_ITERATION', '001')
if ITERATION not in {'001', '002', '003', '004'}:
    raise RuntimeError('UNREVIEWED_TEST_ITERATION')
RUN_ROOT = ROOT/'p3_offline_results'/('iteration_'+ITERATION)
RUN_ROOT.parent.mkdir(exist_ok=True)
RUN_ROOT.mkdir(exist_ok=False)
WRITES = []
def observe_open(event, args):
    if event == 'open' and len(args) >= 3:
        path, mode, flags = args
        if isinstance(path, str) and (isinstance(mode, str) and any(x in mode for x in 'wax+')
                                      or isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR)):
            WRITES.append(str(Path(path).absolute()))
sys.addaudithook(observe_open)


def changed_body(table, entry):
    sink = io.BytesIO()
    pq.write_table(table, sink)
    b = sink.getvalue()
    e = copy.deepcopy(entry)
    e['source'].update(bytes=len(b), sha256=c.sha(b))
    return b, e


class PositionTests(unittest.TestCase):
    def test_valid_partition(self):
        c.check_positions([0, 2], [1], 3)

    def test_duplicate_admitted(self):
        with self.assertRaisesRegex(c.Blocked, 'REPEATED_POSITION'):
            c.check_positions([0, 0], [], 2)

    def test_duplicate_quarantine(self):
        with self.assertRaisesRegex(c.Blocked, 'REPEATED_POSITION'):
            c.check_positions([0], [1, 1], 2)

    def test_negative_position(self):
        with self.assertRaises(c.Blocked):
            c.check_positions([-1, 0], [], 2)

    def test_out_of_bounds(self):
        with self.assertRaises(c.Blocked):
            c.check_positions([0, 2], [], 2)

    def test_missing_position(self):
        with self.assertRaises(c.Blocked):
            c.check_positions([0], [], 2)

    def test_intersection(self):
        with self.assertRaises(c.Blocked):
            c.check_positions([0, 1], [1], 2)

    def test_bool_position(self):
        with self.assertRaisesRegex(c.Blocked, 'POSITION_NOT_INT'):
            c.check_positions([False, 1], [], 2)


class DecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a = json.loads((EVIDENCE / 'ADMISSION_R5.json').read_bytes())
        cls.entry = a['entries'][0]
        cls.body = (EVIDENCE / '2026-09-28_00000.parquet').read_bytes()
        cls.table = pq.ParquetFile(io.BytesIO(cls.body)).read()

    def reject_change(self, column, array, message):
        i = self.table.column_names.index(column)
        t = self.table.set_column(i, column, array)
        b, e = changed_body(t, self.entry)
        with self.assertRaisesRegex(c.Blocked, message):
            c.decode(b, e)

    def test_real_types_and_saved_index(self):
        t, audit = c.decode(self.body, self.entry)
        self.assertEqual(t.num_rows, 80)
        self.assertTrue(audit['saved_index_matches_physical_position'])
        self.assertIn('nanoseconds', audit['footer_schema'])

    def test_one_byte_corruption(self):
        with self.assertRaisesRegex(c.Blocked, 'SOURCE_IDENTITY'):
            c.decode(self.body[:-1] + bytes([self.body[-1] ^ 1]), self.entry)

    def test_length_mismatch(self):
        with self.assertRaisesRegex(c.Blocked, 'SOURCE_IDENTITY'):
            c.decode(self.body + b'0', self.entry)

    def test_saved_index_is_not_physical_order(self):
        self.reject_change('__index_level_0__', pa.array(list(reversed(range(80)))), 'INDEX_POSITION')

    def test_repeated_saved_index(self):
        self.reject_change('__index_level_0__', pa.array([0] * 80), 'INDEX_POSITION')

    def test_integer_date_axis(self):
        self.reject_change('time', pa.array(list(range(80)), type=pa.int64()), 'RAW_ARROW_SCHEMA')

    def test_seconds_not_silently_rescaled(self):
        self.reject_change('time', self.table['time'].cast(pa.timestamp('s')), 'RAW_ARROW_SCHEMA')

    def test_milliseconds_not_silently_rescaled(self):
        self.reject_change('time', self.table['time'].cast(pa.timestamp('ms')), 'RAW_ARROW_SCHEMA')

    def test_microseconds_not_silently_rescaled(self):
        self.reject_change('time', self.table['time'].cast(pa.timestamp('us')), 'RAW_ARROW_SCHEMA')

    def test_non_midnight_time(self):
        self.reject_change('time', pa.array([pd.Timestamp('2026-09-28 15:00')] * 80,
                                          type=pa.timestamp('ns')), 'EXACT_DATE')

    def test_wrong_date(self):
        e = copy.deepcopy(self.entry)
        e['date'] = '2026-09-29'
        with self.assertRaisesRegex(c.Blocked, 'EXACT_DATE'):
            c.decode(self.body, e)

    def test_null_key(self):
        self.reject_change('code', pa.array([None] * 80, type=pa.string()), 'NULL_KEY')

    def test_wrong_supplier_namespace(self):
        self.reject_change('code', pa.array(['600000.SH'] * 80), 'JQ_CODE_NAMESPACE')

    def test_numeric_code_not_cast_to_string(self):
        self.reject_change('code', pa.array([600000] * 80), 'RAW_ARROW_SCHEMA')

    def test_null_live_price_not_filled(self):
        self.reject_change('close', pa.array([None] * 80, type=pa.float64()), 'ADMITTED_NULL')

    def test_inf_not_hidden(self):
        self.reject_change('factor', pa.array([float('inf')] * 80), 'NONFINITE')

    def test_null_factor_rejected(self):
        self.reject_change('factor', pa.array([None] * 80, type=pa.float64()), 'ADMITTED_NULL')

    def test_non_one_factor_preserved_not_adjusted(self):
        t = self.table.set_column(self.table.column_names.index('factor'), 'factor', pa.array([2.5]*80))
        b, e = changed_body(t, self.entry)
        got, _ = c.decode(b, e)
        self.assertEqual(got['factor'].to_pylist(), [2.5]*80)
        self.assertTrue(got['close'].equals(self.table['close']))

    def test_zero_negative_factor_are_facts_not_thresholds(self):
        f = self.table.select(c.FIELDS).to_pandas()
        f.loc[0, 'factor'] = 0.0
        f.loc[1, 'factor'] = -1.0
        r = c.observations(f)['factor']
        self.assertEqual((r['zero'], r['negative'], r['one']), (1, 1, 78))

    def test_extra_field(self):
        b, e = changed_body(self.table.append_column('extra', pa.array([1]*80)), self.entry)
        with self.assertRaisesRegex(c.Blocked, 'RAW_COLUMNS'):
            c.decode(b, e)

    def test_missing_field(self):
        b, e = changed_body(self.table.drop(['money']), self.entry)
        with self.assertRaisesRegex(c.Blocked, 'RAW_COLUMNS'):
            c.decode(b, e)

    def test_duplicate_key_rejected_before_original_reader(self):
        t = pa.concat_tables([self.table.select(c.FIELDS)]*2)
        with self.assertRaisesRegex(c.Blocked, 'DUPLICATE_KEY'):
            c.reject_duplicates(t)

    def test_projection_exact_roundtrip(self):
        raw = self.table.select(c.FIELDS).replace_schema_metadata(None)
        view = c.dictionary_view(raw)
        self.assertEqual(view.column_names[:2], ['trade_date', 'symbol'])
        self.assertTrue(view.rename_columns(c.FIELDS).equals(raw))


class GuardTests(unittest.TestCase):
    def test_path_traversal(self):
        for bad in ['../a', '/a', 'C:/a', 'a\\b', 'a/../b', 'a//b', './a']:
            with self.subTest(bad=bad), self.assertRaises(c.Blocked):
                c.relative(bad)

    def test_no_unregistered_root(self):
        with self.assertRaisesRegex(c.Blocked, 'SOURCE_ROOT_NOT_BOUND'):
            c.source_key({'source': {'path': r'E:\OTHER\raw\stock\a.parquet'}}, BINDINGS)

    def test_generation_cannot_move_to_new_root(self):
        class BoundReader:
            bindings = BINDINGS
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'first', Path(d)/'second'
            gen = c.generation_for(a,BINDINGS)
            self.assertNotEqual(gen,c.generation_for(b,BINDINGS))
            with self.assertRaisesRegex(c.Blocked,'GENERATION_ROOT_CODE_BINDING'):
                c.build(BoundReader(),b,gen)
            self.assertFalse(b.exists())

    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'source').write_text('x')
            (p/'alias').symlink_to(p/'source')
            with self.assertRaisesRegex(c.Blocked, 'SOURCE_SYMLINK'):
                c.read_regular(p/'alias')

    def test_pinned_file_changed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'x.json';p.write_text('{}')
            with self.assertRaisesRegex(c.Blocked, 'INPUT_IDENTITY'):
                c.load_pinned(p, {'bytes':2, 'sha256':'0'*64})

    def test_bound_dictionary_change_rejected(self):
        pin = dict(BINDINGS['domain_contract'], sha256='0'*64)
        with self.assertRaisesRegex(c.Blocked, 'INPUT_IDENTITY'):
            c.verify_identity(EVIDENCE/pin['name'],pin)

    def test_bound_consumer_change_rejected(self):
        pin = dict(BINDINGS['original_consumer'], sha256='0'*64)
        with self.assertRaisesRegex(c.Blocked, 'INPUT_IDENTITY'):
            c.verify_identity(EVIDENCE/pin['name'],pin)

    def test_output_input_storage_drift(self):
        # A correct identity rejects a changed storage byte, with no fallback.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'archive';p.write_bytes(b'original')
            pin = {'bytes':8,'sha256':c.sha(b'original')}
            p.write_bytes(b'changed!')
            with self.assertRaisesRegex(c.Blocked, 'INPUT_IDENTITY'):
                c.verify_identity(p,pin)

    def test_no_backtest_access_even_with_date_equal(self):
        for purpose in ['BACKTEST', 'SAME_DAY_EOD', 'NEXT_DAY', 'LIVE', 'FACTOR_RESEARCH']:
            with self.subTest(purpose=purpose), self.assertRaisesRegex(c.Blocked, 'USE_NOT_ADMITTED'):
                c.read_candidate('/does/not/exist', 'SAME_ASOF', 'stock', purpose)

    def test_no_old_side_effect_imports(self):
        tree = ast.parse(Path(c.__file__).read_text())
        imports = {n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import)}
        self.assertFalse(imports & {'requests','urllib','jqdatasdk','subprocess','shutil','sqlite3'})
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls & {'unlink','remove','replace','rename','link','system','rmtree','glob'})


class FullBodyTests(unittest.TestCase):
    def test_full_real_body_build_and_independent_audit(self):
        reader = c.BodyReader(EVIDENCE, BINDINGS)
        result_root = RUN_ROOT/'full_body'
        report = c.build(reader, result_root, c.generation_for(result_root,BINDINGS))
        self.assertEqual(report['conservation'], {'input':117461, 'output':117460, 'excluded':1})
        self.assertFalse(report['backtest_admission'])
        self.assertEqual(report['facts']['raw']['paused_1_ohlc_eq_pre_close_volume_money_zero'],192)
        self.assertEqual(report['facts']['raw']['factor']['one'],117461)
        # Independent expected tables: read physical columns without calling decoder or build helpers.
        expected, original_parts = {}, {}
        for entry, key in zip(reader.admission['entries'], reader.entry_keys):
            b = reader.read(entry, key)
            raw = pq.ParquetFile(io.BytesIO(b)).read().select(c.FIELDS).replace_schema_metadata(None)
            original_parts[entry['source']['path']] = raw
            cell = entry['product'], entry['date']
            selected = raw.take(pa.array(entry['admitted_positions'], pa.int64()))
            expected.setdefault(cell, []).append(selected)
        total = 0
        for row in report['outputs']:
            table = pq.ParquetFile(result_root/row['path']).read().replace_schema_metadata(None)
            wanted = pa.concat_tables(expected[(row['product'],row['date'])])
            self.assertTrue(table.equals(wanted), row['path'])
            lines = json.loads((result_root/'lineage'/row['product']/(row['date']+'.json')).read_bytes())
            sources = json.loads((result_root/'SOURCES.json').read_bytes())
            self.assertEqual(len(lines),len(table))
            for position, line in enumerate(lines):
                s = sources[line['source_id']]
                self.assertEqual(line['source_sha256'],s['sha256'])
                source_row = original_parts[s['path']].slice(line['physical_row_position'],1)
                self.assertTrue(table.slice(position,1).equals(source_row))
                self.assertEqual(line['output_row_position'],position)
            total += len(table)
        self.assertEqual(total,117460)
        # Isolate the actual pure reader function by AST, without module imports or main.
        source_path = EVIDENCE / BINDINGS['original_consumer']['name']
        raw_source = source_path.read_bytes()
        self.assertEqual(c.sha(raw_source), BINDINGS['original_consumer']['sha256'])
        syntax = ast.parse(raw_source.decode('utf-8-sig'))
        fn = next(n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name=='read_price_frame')
        mod = ast.Module(body=[fn], type_ignores=[])
        namespace = {'pd':pd,'Path':Path,'Optional':Optional,
                     'log':lambda text: (_ for _ in ()).throw(AssertionError(text))}
        exec(compile(mod,str(source_path),'exec'), namespace)
        compatibility = {}
        for product in c.FAMILIES:
            paths = [result_root/r['path'] for r in report['outputs'] if r['product']==product]
            original = namespace['read_price_frame'](paths, max_files=None)
            target = c.read_candidate(result_root,report['generation'],product,'OFFLINE_VALUE_AUDIT').to_pandas()
            projected = target[['time','code','open','high','low','close','volume','money']].rename(columns={'time':'date'})
            projected = projected.sort_values(['code','date']).reset_index(drop=True)
            pd.testing.assert_frame_equal(original.reset_index(drop=True),projected)
            compatibility[product] = {'rows':len(original),'value_projection':'EXACT',
                'PIT_admission':False,'full_engine_acceptance':False,
                'function':'read_price_frame','original_source_sha256':c.sha(raw_source)}
        c.write_new(RUN_ROOT/'CONSUMER_COMPATIBILITY.json',c.packed(compatibility))
        c.write_new(RUN_ROOT/'INDEPENDENT_FULL_BODY_AUDIT.json',c.packed({
            'input_files':1504,'physical_input_rows':117461,'candidate_rows_compared':total,
            'all_14_fields_exact':True,'all_row_lineage_exact':True,
            'admitted_cells':len(expected),'quarantined':1,
            'historical_pit':'NOT_ESTABLISHED','native_execution':'NOT_ISSUED'}))
        # Existing-generation collision must not overwrite any byte.
        before = (result_root/'MANIFEST.json').read_bytes()
        with self.assertRaisesRegex(c.Blocked,'OUTPUT_EXISTS'):
            c.build(reader,result_root,report['generation'])
        self.assertEqual((result_root/'MANIFEST.json').read_bytes(),before)
        # Inject write failure; partial output is retained and can never look complete.
        failure_root = RUN_ROOT/'injected_failure'
        original_write = c.parquet_new
        n = [0]
        def fail_second(*args):
            n[0] += 1
            if n[0] == 2:
                raise OSError('INJECTED_SECOND_OUTPUT_FAILURE')
            return original_write(*args)
        with patch.object(c,'parquet_new',fail_second), self.assertRaisesRegex(OSError,'INJECTED'):
            c.build(reader,failure_root,c.generation_for(failure_root,BINDINGS))
        self.assertTrue((failure_root/'FAILED.json').is_file())
        self.assertFalse((failure_root/'BUILD_COMPLETE.json').exists())
        # Candidate tamper is checked on a disposable copy, preserving full-body result.
        with tempfile.TemporaryDirectory() as d:
            damaged = Path(d)/'tampered';shutil.copytree(result_root,damaged)
            p = damaged/report['outputs'][0]['path'];p.write_bytes(p.read_bytes()+b'0')
            with self.assertRaisesRegex(c.Blocked,'CANDIDATE_IDENTITY'):
                c.read_candidate(damaged,report['generation'],'stock','OFFLINE_VALUE_AUDIT')
        with self.assertRaisesRegex(c.Blocked,'GENERATION_BINDING'):
            c.verify_candidate(result_root,'ANOTHER_GENERATION')
        self.assertFalse(any(str(EVIDENCE.resolve()) in p for p in WRITES))
        self.assertFalse(any(p.upper().startswith(('E:', 'C:')) for p in WRITES))
        c.write_new(RUN_ROOT/'OBSERVED_WRITE_PATHS.json',c.packed({
            'scope':'GPT Linux test process open-write audit events, not native OS process audit',
            'paths':sorted(set(WRITES)), 'evidence_source_write_opens':0,
            'windows_business_tree_write_opens':0}))


if __name__ == '__main__':
    unittest.main(verbosity=2)

import ast
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
from r10_pagination_candidate import RequestSpec, paginate_in_memory, verify_replay

PIN = '978aedee181eac7815daed14a5b057f4ab3f8c663afa6f8c18e541561a02beae'

def legacy_pure():
    raw = Path(__file__).with_name('legacy_original.py').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('LEGACY_PIN_MISMATCH')
    tree = ast.parse(raw)
    names = {'RequestSpec','PageReceipt','AcquisitionReceipt','_row_key','_sha_rows','paginate_in_memory'}
    nodes = [n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    module = types.ModuleType('r10_legacy_pure'); sys.modules[module.__name__] = module
    exec('from __future__ import annotations\nimport json, hashlib\nfrom dataclasses import dataclass, field\nfrom typing import Optional\nDEFAULT_PAGE_SIZE=4000', module.__dict__)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pinned-pure-AST>','exec'),module.__dict__)
    return module

def spec(n=None, page=4):
    return RequestSpec('SYNTHETIC','fixture',['id'],['id'],page,n)

def rows(n):
    return [{'id':i,'value':10} for i in range(n)]

class Checks(unittest.TestCase):
    def test_legacy_shortfall_false_pass(self):
        m=legacy_pure(); r=m.paginate_in_memory(rows(2),m.RequestSpec('SYNTHETIC','fixture',['id'],['id'],4,3))
        self.assertTrue(r.hard_gates_pass);self.assertEqual(r.REPLAY_IDENTICAL,'NOT_TESTED')
    def test_partial_page_shortfall(self):
        self.assertFalse(verify_replay(rows(2),rows(2),spec(3)).hard_gates_pass)
    def test_empty_positive_minimum(self):
        self.assertEqual(verify_replay([],[],spec(1)).SILENT_TRUNCATION,1)
    def test_multi_page_shortfall(self):
        self.assertFalse(verify_replay(rows(9),rows(9),spec(10)).hard_gates_pass)
    def test_not_tested_blocks(self):
        self.assertFalse(paginate_in_memory(rows(3),spec(3)).hard_gates_pass)
    def test_equal_replay(self):
        self.assertTrue(verify_replay(rows(9),rows(9),spec(9)).hard_gates_pass)
    def test_changed_value_replay(self):
        a=rows(3);b=rows(3);b[1]['value']=11
        self.assertEqual(verify_replay(a,b,spec(3)).REPLAY_IDENTICAL,'NO')
    def test_changed_count_replay(self):
        self.assertFalse(verify_replay(rows(3),rows(2),spec()).hard_gates_pass)
    def test_duplicate_within_page(self):
        a=[{'id':1},{'id':1}];self.assertFalse(verify_replay(a,a,spec()).hard_gates_pass)
    def test_duplicate_across_pages(self):
        a=rows(4)+[{'id':3}];self.assertFalse(verify_replay(a,a,spec(5)).hard_gates_pass)
    def test_full_page_without_authority_preserves_block(self):
        self.assertFalse(verify_replay(rows(4),rows(4),spec()).hard_gates_pass)
    def test_declared_minimum_exact_multiple(self):
        self.assertTrue(verify_replay(rows(8),rows(8),spec(8)).hard_gates_pass)
    def test_invalid_page_sizes(self):
        for size in [0,-1,True,1.5]:
            with self.subTest(size=size),self.assertRaises(ValueError):paginate_in_memory([],spec(page=size))
    def test_invalid_minimum(self):
        for n in [-1,True,1.5]:
            with self.subTest(n=n),self.assertRaises(ValueError):paginate_in_memory([],spec(n))
    def test_missing_and_null_keys(self):
        for a in [[{}],[{'id':None}]]:
            with self.subTest(a=a),self.assertRaises(ValueError):paginate_in_memory(a,spec())
    def test_empty_key_contract(self):
        s=spec();s.primary_key=[]
        with self.assertRaises(ValueError):paginate_in_memory([],s)
    def test_composite_delimiter_collision(self):
        s=RequestSpec('SYNTHETIC','fixture',['a','b'],['a','b'],4,2)
        a=[{'a':'a|b','b':'c'},{'a':'a','b':'b|c'}]
        self.assertTrue(verify_replay(a,a,s).hard_gates_pass)
    def test_typed_key_collision(self):
        a=[{'id':1},{'id':'1'}];self.assertTrue(verify_replay(a,a,spec(2)).hard_gates_pass)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful(),'scope':'OFFLINE_LIST_MODEL_ONLY','supplier_calls':0,'FOUNDATION_ACCEPTANCE':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)

"""Generate GPT-owned, bounded safety edits; never modify the supplied R03 tree."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def norm(text):
    return text.replace('\r\n', '\n').rstrip('\n') + '\n'


def digest(text):
    return hashlib.sha256(norm(text).encode('utf-8')).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('PATCH_ANCHOR_MISMATCH')
    return text.replace(old, new, 1)


def patched_adapter(text):
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'EngineLocalValueProvider')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_envelope_or_raise')
    lines = text.splitlines(keepends=True)
    body = '''    def _envelope_or_raise(self, env, *, allow_partial=False):
        self.last_envelope = env
        # Diagnostic envelopes may be partial; the engine boundary must not be.
        status = env.get("status")
        reasons = list(env.get("incomplete_reasons") or [])
        if status != Reason.OK or reasons:
            raise ProviderReject(env.get("reason") or "ENGINE_ADMISSION_NOT_COMPLETE",
                                 {"status": status, "incomplete_reasons": reasons})
        denied = [f for f, a in (env.get("field_admission") or {}).items()
                  if a.get("admitted") is not True]
        if denied:
            raise ProviderReject("ENGINE_REQUESTED_FIELD_NOT_ADMITTED", {"fields": denied})
        if env.get("coverage") is not None and env["coverage"].get("proven") is not True:
            raise ProviderReject("ENGINE_COVERAGE_UNPROVEN", {})
        accounting = env.get("file_accounting") or {}
        if any(accounting.get(k) for k in ("unreadable", "schema_conflict", "budget_skipped", "truncated_rows")):
            raise ProviderReject("ENGINE_SOURCE_ACCOUNTING_INCOMPLETE", {})
        return env
'''
    text = ''.join(lines[:method.lineno-1]) + body + ''.join(lines[method.end_lineno:])
    text = replace_once(text, 'strict_partial: bool = False', 'strict_partial: bool = True')
    text = replace_once(text, 'self.strict_partial = strict_partial', 'self.strict_partial = True  # caller cannot relax admission')
    text = replace_once(text, '        self.last_envelope = env\n        df = env.get("df")',
                        '        self._envelope_or_raise(env)\n        df = env.get("df")')
    # These methods need authoritative PIT, units and historical membership contracts.
    # The diagnostic reader remains available; it is not engine admission evidence.
    for name, guard in [('get_index_stocks', 'ENGINE_INDEX_CONTRACT_PENDING'),
                        ('get_split_dividend', 'ENGINE_EVENT_CONTRACT_PENDING')]:
        tree = ast.parse(text)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'EngineLocalValueProvider')
        node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            first = node.body[1]
        lines = text.splitlines(keepends=True)
        lines.insert(first.lineno-1, '        raise ProviderReject("' + guard + '", {"scope": "candidate engine admission; contract review pending"})\n')
        text = ''.join(lines)
    text = text.replace('* Rejected envelopes raise; partial envelopes are returned but always carry',
                        '* Rejected and partial envelopes both raise before an engine result is returned.\n* Diagnostic metadata on successful frames includes')
    return text


def patched_provider(text):
    text = replace_once(text,
        '        rows, withheld = [], 0\n',
        '        rows, withheld, withheld_future = [], 0, 0\n')
    text = replace_once(text,
        '            rows.append({"code": r.get("code"),\n',
        '            if asof_d and ann is not None and ann > asof_d:\n'
        '                withheld_future += 1\n'
        '                continue\n'
        '            rows.append({"code": r.get("code"),\n')
    text = replace_once(text,
        '        if accounting["unreadable"]:\n            reasons.append(Reason.SOURCE_FILE_UNREADABLE)\n',
        '        if accounting["unreadable"]:\n            reasons.append(Reason.SOURCE_FILE_UNREADABLE)\n'
        '        if accounting["budget_skipped"]:\n            reasons.append(Reason.FILE_BUDGET_EXCEEDED)\n')
    text = replace_once(text,
        '                "withheld_unknown_announcement": withheld,\n',
        '                "withheld_unknown_announcement": withheld,\n'
        '                "withheld_future_announcement": withheld_future,\n')
    return text


def main():
    source, destination, manifest_file = map(Path, sys.argv[1:])
    expected = json.loads(manifest_file.read_text(encoding='utf-8'))['normalized_sha256']
    if destination.exists():
        raise SystemExit('DESTINATION_ALREADY_EXISTS')
    texts = {f: norm((source / f).read_text(encoding='utf-8-sig')) for f in expected}
    for f, text in texts.items():
        if digest(text) != expected[f]:
            raise SystemExit('SOURCE_HASH_MISMATCH:' + f)
    texts['engine_adapter.py'] = patched_adapter(texts['engine_adapter.py'])
    texts['provider.py'] = patched_provider(texts['provider.py'])
    for text in texts.values():
        ast.parse(text)
    destination.mkdir(parents=True)
    for f, text in texts.items():
        (destination / f).write_text(text, encoding='utf-8')
    (destination / '__init__.py').write_text('"""R04 candidate; GPT safety patch only."""\n', encoding='utf-8')
    print(json.dumps({'status': 'PATCH_CREATED', 'normalized_sha256': {f: digest(t) for f, t in texts.items()}}))


if __name__ == '__main__':
    main()

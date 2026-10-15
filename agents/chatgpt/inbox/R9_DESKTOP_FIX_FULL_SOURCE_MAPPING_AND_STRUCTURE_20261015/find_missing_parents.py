# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_formal_chain as chain
p = chain.CANDIDATE_PLAN
conn = sqlite3.connect(f"file:{p.resolve().as_posix()}?mode=ro", uri=True)
directories = set()
dest_directories = set()
for path, is_dir, is_reparse in conn.execute("SELECT path, is_dir, is_reparse FROM paths"):
    if int(is_reparse) or not int(is_dir):
        continue
    key = chain._path_key(path)
    directories.add(key)
    dest_directories.add(chain._dest_inventory_key(path))
known = {chain._path_key(root) for root in ("E:\\BLACKBOX", "E:\\BLACKBOX_ENGINES", "D:")}
print("dir_missing")
for key in directories:
    if chain._parent_missing(key, directories, known):
        print("DIR", key)
print("file_missing")
shown = 0
count = 0
cur = conn.execute("SELECT path FROM paths WHERE is_dir=0 AND is_reparse=0")
while True:
    rows = cur.fetchmany(20000)
    if not rows:
        break
    for (path,) in rows:
        if chain._parent_missing(path, directories, known):
            count += 1
            if shown < 30:
                print(path)
                shown += 1
print("file_missing_count", count)
print("link_missing")
for path, target, migrated_link, migrated_target in conn.execute("SELECT path, target, migrated_link_path, migrated_target FROM links"):
    inventory = str(path).replace("/", "\\").rstrip("\\")
    link_path = str(migrated_link or path).replace("/", "\\").rstrip("\\")
    dest_parent = link_path.rsplit("\\", 1)[0]
    inv_bad = chain._parent_missing(inventory, directories, known)
    dest_bad = chain._path_key(dest_parent) not in dest_directories and chain._path_key(dest_parent) not in known and len(dest_parent) > 3
    if inv_bad or dest_bad:
        print("LINK", inv_bad, dest_bad, inventory)
conn.close()

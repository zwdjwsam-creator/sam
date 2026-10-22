# registry writes in cache_compiler_daily_incremental_r1.py
sha=c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336

L124: def write_static_registries() -> None:
L143: CACHE_MANIFEST_REGISTRY_R1,META,ALL,ACTIVE,n/a,Manifest registry
L144: CACHE_DEPENDENCY_REGISTRY_R1,META,ALL,ACTIVE,n/a,Dependency registry
L229: wjson(REGISTRY / "CACHE_DEPENDENCY_REGISTRY.json", dep)
L405: write_static_registries()
L608: wjson(REGISTRY / "CACHE_MANIFEST_REGISTRY.json", {
L614: json.loads((REGISTRY / "CACHE_DEPENDENCY_REGISTRY.json").read_text(encoding="utf-8")))
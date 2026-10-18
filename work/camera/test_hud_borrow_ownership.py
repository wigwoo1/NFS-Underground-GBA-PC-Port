import ctypes as C,sys,runpy,json
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-borrow-20261008')
sys.argv=['test','work/camera/prototype-runs/owned-native-1791430642217389200.json',str(cp/'fullscene-parity.json')]
ns=runpy.run_path('work/camera/test_hud_borrow_4k.py');d=ns['gpu'];d.nf_hud_view_stats.argtypes=[C.c_void_p];stats=(C.c_uint64*3)();assert d.nf_hud_view_stats(stats)
assert stats[0]>=4 and stats[2]==0,list(stats)
(cp/'ownership.json').write_text(json.dumps(dict(result='PASS',stats=list(stats),scope='Four exact full4K segmented draws borrowed retained possibly unaligned HUD tail. API returned with no active borrowed view; close/GC and malformed tail covered by parity test. Packed view preserves serialized offsets; nonsegmented copy path verified separately.'),indent=2));print('PASS borrowed HUD ownership',list(stats))

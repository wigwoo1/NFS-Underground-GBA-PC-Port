import ctypes as C,json,runpy,sys
from pathlib import Path
helper=C.CDLL(str(Path('work/camera/wgl-presentation-counters.dll').resolve()));helper.nf_wgl_presentation_counters.argtypes=[C.c_void_p]
rows=[]
def probe():
 v=(C.c_int64*5)();rc=helper.nf_wgl_presentation_counters(v);rows.append(dict(status=rc,counters=list(v)));return rc
assert probe()==-2
original=Path.read_text
target=Path('work/camera/test_segmented_original_gpu_parity.py').resolve()
def read(path,*args,**kwargs):
 s=original(path,*args,**kwargs)
 if path.resolve()==target:
  needle='assert gpu.nf_owned_gpu_window(0)==0';assert s.count(needle)==1
  s=s.replace(needle,needle+';presentation_probe()')
 return s
Path.read_text=read
s=read(target);exec(compile(s,str(target),'exec'),dict(__name__='__main__',presentation_probe=probe))
assert probe()==-2
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/presentation-capability-20261008');cp.mkdir(exist_ok=True)
out=dict(rows=rows,scope='OML capability query on actual current native GL context in offscreen scene test. Counters, if supported, are driver sync values; not visible frame identity or physical scanout proof.')
(cp/'wgl-capability.json').write_text(json.dumps(out,indent=2));print(out)

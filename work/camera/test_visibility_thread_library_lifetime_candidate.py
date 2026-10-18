import ctypes as C,threading,weakref,gc,json
from pathlib import Path
import owned_visibility_thread_library_install_candidate as install
from owned_model_record_builder import ModelRecordBuilder
rom=bytes(0x647700);a=ModelRecordBuilder(rom);b=ModelRecordBuilder(rom)
assert a.lib is b.lib and a.reciprocal is not b.reciprocal and a._scene_memory is not b._scene_memory
before=b.reciprocal.raw;a.reciprocal[0]=b'\x7f';assert b.reciprocal.raw==before
ref=weakref.ref(a.lib);a=b=None;gc.collect();assert ref() is install.visibility_library()
barrier=threading.Barrier(3);identities=[];errors=[]
def run():
 try:
  x=ModelRecordBuilder(rom);y=ModelRecordBuilder(rom);assert x.lib is y.lib
  identities.append(id(x.lib));barrier.wait(5);barrier.wait(5)
 except BaseException as e:errors.append(str(e));barrier.abort()
threads=[threading.Thread(target=run) for _ in range(2)]
for t in threads:t.start()
barrier.wait(5);assert len(set(identities+[id(ref())]))==3;barrier.wait(5)
for t in threads:t.join(5);assert not t.is_alive()
assert not errors,errors
gc.collect()
out=dict(result='PASS_VISIBILITY_THREAD_LIBRARY_PRIVATE_BUILDER_LIFETIME',threads=3,private_reciprocal_mutation_isolation=True,scope='Per-thread wrapper reuse, distinct concurrent wrappers, private ROM-derived reciprocal arrays and scene containers. Captured queued parity tested separately; no live performance proof.')
Path('work/camera/prototype-runs/visibility-thread-library-lifetime-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])

"""Copy exact ctypes arrays with native memmove, preserving private ownership."""
import ctypes as C
from pathlib import Path
import owned_source_draw_context_candidate as original
source=Path(original.__file__).read_text()
needle='  clone=lambda t,x:(t*len(x))(*x)'
assert source.count(needle)==1
source=source.replace(needle,'  clone=clone_array')
copy_counts={"bulk":0,"fallback":0}
def clone_array(t,x):
 if isinstance(x,C.Array) and x._type_ is t:
  copy_counts["bulk"]+=1
  copied=(t*len(x))();C.memmove(copied,x,C.sizeof(copied));return copied
 copy_counts["fallback"]+=1
 return (t*len(x))(*x)
ns=dict(__name__=__name__,clone_array=clone_array);exec(compile(source,str(Path(__file__)),'exec'),ns)
ns['SourceDrawContext']=original.SourceDrawContext
OwnedSourceDraw=ns['OwnedSourceDraw'];SourceDrawContext=original.SourceDrawContext
def install():
 import owned_segmented_source_draw_candidate as segmented
 source=Path(segmented.__file__).read_text().replace('from owned_source_draw_context_candidate import','from owned_source_array_copy_candidate import')
 scope=dict(__name__=__name__);exec(compile(source,segmented.__file__,'exec'),scope)
 import owned_segmented_source_batch as batch
 segmented.OwnedSegmentedSourceDraw=scope['OwnedSegmentedSourceDraw']
 batch.OwnedSourceDraw=segmented.OwnedSegmentedSourceDraw



"""Same sidecar validation, allocation-light source extent walk."""
import inspect,textwrap
import owned_source_process_sidecar_candidate as base
from owned_source_extent_decode_candidate import extents
source=textwrap.dedent(inspect.getsource(base.decode))
source=source.replace("scene=_decode_records(samples[alpha][0],source_keys=False);sources=scene['records'];n=len(sources)","epoch,refresh,face_counts=extents(samples[alpha][0]);n=len(face_counts)")
source=source.replace("scene['epoch']",'epoch').replace("scene['refresh']",'refresh')
source=source.replace('for i,source in enumerate(sources):','for i,faces in enumerate(face_counts):').replace("   faces=len(source['blocks'][5]) if source['kind']==3 else 0\n",'')
namespace=dict(base.decode.__globals__,extents=extents)
exec(compile(source,'source-extent-sidecar','exec'),namespace)
decode=namespace['decode']

"""Single-allocation road GPU record; original fields and guards retained."""
import inspect,textwrap
from owned_complete_road_gpu import encode_road as original
source=textwrap.dedent(inspect.getsource(original));needle="return struct.pack('<4I',0x3147534e,1,0,12)+b''.join(struct.pack('<I',len(b))+b for b in blocks)";assert source.count(needle)==1
source=source.replace(needle,"return b''.join((struct.pack('<4I',0x3147534e,1,0,12),*(part for b in blocks for part in (struct.pack('<I',len(b)),b))))")
ns=dict(original.__globals__);exec(compile(source,'single-allocation-road-record','exec'),ns);encode_road=ns['encode_road']

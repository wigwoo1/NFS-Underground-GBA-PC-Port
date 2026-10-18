"""Default-off recv clone preserving original publication guards."""
import inspect,textwrap
import owned_progressive_shared_transport_candidate as transport
from owned_direct_shared_input_decode_candidate import decode_private
original=transport.SharedInputConnection.recv
source=inspect.getsource(original)
needle='payload=bytes(self.memory.buf[:size]);copied=time.perf_counter_ns() if trace else None\n   request=pickle.loads(payload);decoded=time.perf_counter_ns() if trace else None'
assert source.count(needle)==1
source=source.replace(needle,'copied=begin\n   request=decode_private(self.memory,size);decoded=time.perf_counter_ns() if trace else None')
source=source.replace('payload_bytes=size,serial=serial)','payload_bytes=size,serial=serial,direct_shared_decode=True)')
namespace=dict(original.__globals__,decode_private=decode_private)
exec(compile(textwrap.dedent(source),'direct-private-shared-input-decode','exec'),namespace)
transport.SharedInputConnection.recv=namespace['recv']

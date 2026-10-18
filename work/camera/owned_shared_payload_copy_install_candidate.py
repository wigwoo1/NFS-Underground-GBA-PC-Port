"""Experimental parent-only input copy; same serialization and publication ordering."""
import inspect
import owned_progressive_shared_transport_candidate as transport
from owned_shared_payload_copy_binding_candidate import copy_payload
source=inspect.getsource(transport.SharedInputConnection.send)
needle='self.memory.buf[:len(payload)]=payload';assert source.count(needle)==1
source=source.replace(needle,'copy_payload(self.memory,payload)').replace('payload_bytes=len(payload))','payload_bytes=len(payload),native_copy=True)')
import textwrap
namespace=dict(transport.SharedInputConnection.send.__globals__,copy_payload=copy_payload)
exec(compile(textwrap.dedent(source),'native-input-payload-copy','exec'),namespace)
transport.SharedInputConnection.send=namespace['send']

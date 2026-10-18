import inspect,textwrap
import owned_progressive_shared_transport_candidate as transport
from owned_shared_input_read_copy_candidate import copy_private
source=inspect.getsource(transport.SharedInputConnection.recv)
needle='payload=bytes(self.memory.buf[:size])';assert source.count(needle)==1
source=source.replace(needle,'payload=copy_private(self.memory,size)').replace('serial=serial)','serial=serial,native_private_copy=True)')
namespace=dict(transport.SharedInputConnection.recv.__globals__,copy_private=copy_private)
exec(compile(textwrap.dedent(source),'native-private-input-read','exec'),namespace)
transport.SharedInputConnection.recv=namespace['recv']

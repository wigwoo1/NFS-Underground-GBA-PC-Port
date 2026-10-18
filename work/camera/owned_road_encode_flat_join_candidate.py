import inspect,textwrap
import owned_complete_road_gpu as road
source=inspect.getsource(road.encode_road)
needle=" return struct.pack('<4I',0x3147534e,1,0,12)+b''.join(struct.pack('<I',len(b))+b for b in blocks)"
assert source.count(needle)==1
source=source.replace(needle," pieces=[struct.pack('<4I',0x3147534e,1,0,12)]\n for block in blocks:pieces.extend((struct.pack('<I',len(block)),block))\n return b''.join(pieces)")
namespace=dict(road.encode_road.__globals__)
exec(compile(textwrap.dedent(source),'road-encode-flat-join','exec'),namespace)
encode_road=namespace['encode_road']

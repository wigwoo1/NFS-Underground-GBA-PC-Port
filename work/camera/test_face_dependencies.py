from pathlib import Path
exec(compile(Path('work/camera/audit_captured_road_recursion.py').read_text().split('checks=[]')[0],'fixture','exec'))
from owned_face_dependencies import face_addresses,encode_faces,decode_faces
scene=scenes[1];addresses=face_addresses(scene.graph)
payload=encode_faces(scene.graph,lambda address,size:struct.pack('<I',address)*5)
assert tuple(sorted(decode_faces(payload,scene.graph)))==addresses
for invalid in (payload[:-1],payload+bytes(24),payload[:16]):
 try:decode_faces(invalid,scene.graph)
 except ValueError:pass
 else:raise AssertionError('Invalid face closure accepted')
print('PASS face closure exact dependency coverage and malformed transport rejection',len(addresses))

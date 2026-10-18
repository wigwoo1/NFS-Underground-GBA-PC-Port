"""Uncut default wall prepared-edge component; unsupported clipping rejects."""
from pathlib import Path
import ctypes as C,struct
p=Path(__file__).resolve().parent
camera=C.CDLL(str(p/'road-camera-continuous.dll')).nf_road_camera_continuous;camera.argtypes=[C.c_void_p]*3
project=C.CDLL(str(p/'road-point-project-continuous.dll')).nf_road_point_project_continuous;project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]+[C.c_void_p]*3
order=C.CDLL(str(p/'wall-edge-order.dll')).nf_wall_edge_order;order.argtypes=[C.c_int,C.c_int,C.c_uint,C.c_void_p]
uv=C.CDLL(str(p/'wall-source-uv.dll')).nf_wall_source_uv;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
def prepared_edge(wall,table):
 assert not wall['extended_uv'],'Extended wall mode unsupported here'
 projected=[]
 for vertex in wall['world_vertices']:
  point=(C.c_double*3)();assert camera((C.c_double*3)(*vertex),bytes.fromhex(wall['camera_hex']),point);assert point[2]>=64,'Near-clipped wall unsupported here';out=(C.c_double*5)();assert project(point,(C.c_int32*2)(0,0),8,128,(C.c_int32*3)(120,87,128),table,out);projected.append((int(out[0]),int(out[1]),int(point[2])))
 ordered=(C.c_int*3)();assert order(projected[0][0],projected[1][0],wall['flags'],ordered);source=bytes.fromhex(wall['source_hex']);animation=bytes.fromhex(wall['animation_hex']);shift=struct.unpack_from('<H',bytes.fromhex(wall['material_hex']),36)[0];values=(C.c_uint32*6)();assert uv(source,animation,shift,wall['flags'],values)
 edge=bytearray(52);struct.pack_into('<8h',edge,0,ordered[0],ordered[1],projected[0][2],projected[1][2],projected[0][1],projected[1][1],projected[3][1],projected[2][1]);struct.pack_into('<6I',edge,16,*values);struct.pack_into('<2H',edge,40,source[60]<<8,source[61]<<8);struct.pack_into('<H',edge,48,ordered[2]);return bytes(edge)


def prepared_edge_owned(blocks,table):
 """Decode complete owned wall endpoints; no emulator reads or prepared-edge input."""
 assert len(blocks)==12 and len(blocks[0])==136 and len(blocks[1])==64 and len(blocks[11])==260
 source,next_source=blocks[0][:68],blocks[0][68:]
 offset,next_offset=blocks[1][:32],blocks[1][32:]
 h=lambda b,o:struct.unpack_from('<h',b,o)[0]
 i=lambda b,o:struct.unpack_from('<i',b,o)[0]
 x,z=i(source,0)+h(offset,0),i(source,4)+h(offset,2)
 nx,nz=i(next_source,0)+h(next_offset,0),i(next_source,4)+h(next_offset,2)
 flags=struct.unpack_from('<I',blocks[11],256)[0]
 wall=dict(world_vertices=[[x,h(source,8)+h(offset,8),z],[nx,h(source,12)+h(offset,8),nz],[nx,h(source,14)+h(offset,10),nz],[x,h(source,10)+h(offset,10),z]],flags=flags,extended_uv=bool(flags&128),camera_hex=blocks[3].hex(),source_hex=source.hex(),animation_hex=blocks[2].hex(),material_hex=blocks[4].hex())
 return prepared_edge(wall,table)

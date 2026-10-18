"""Trilinear extension of recovered original camera-cell model projection.
Classification coordinates only; native raster geometry stays continuous.
"""
import math

def signed32(value):
 value=int(value)&0xffffffff;return value-4294967296 if value&2147483648 else value

def signed16(value):
 value=int(value)&65535;return value-65536 if value&32768 else value

def project_integer_cell(x,y,z,scale,center,table):
 if not 0<=z<=24576:raise ValueError('Original model depth rejection')
 factor=signed32((int(scale)*int(table[z]))&0xffffffff)>>8
 return tuple(signed16(int(c)+(signed32((int(v)*factor)&0xffffffff)>>16)) for v,c in zip((x,y),center))

def project_camera_cells(point,scale,center,table):
 if len(point)!=3 or len(center)!=2 or not all(math.isfinite(v) for v in (*point,*center)) or not 0<=scale<=4294967295 or len(table)<24577:raise ValueError('Invalid camera projection')
 if any(v< -2147483648 or v>2147483646 for v in point[:2]) or not 0<=point[2]<=24576:raise ValueError('Unsupported original model coordinate domain')
 base=tuple(math.floor(v) for v in point);fractions=tuple(v-b for v,b in zip(point,base));result=[0.,0.]
 for ix in (0,1):
  for iy in (0,1):
   for iz in (0,1):
    weight=math.prod(f if offset else 1-f for f,offset in zip(fractions,(ix,iy,iz)))
    if not weight:continue
    sample=project_integer_cell(base[0]+ix,base[1]+iy,base[2]+iz,scale,center,table)
    for axis in (0,1):result[axis]+=weight*sample[axis]
 return tuple(result)

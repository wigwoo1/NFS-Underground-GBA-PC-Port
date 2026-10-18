"""Bounded owned source mask sidecar for process preparation candidates."""
import ctypes as C,struct,math
from owned_motion_pairs import _decode_records

def encode(owner,identity):
 cameras=owner.source_cameras
 payload=dict(version=1,identity=tuple(identity),cameras=struct.pack('<24i24d',*cameras[0],*cameras[1],*cameras[2],*cameras[3]),masks=[(a,bytes(v[0]),bytes(v[1]),v[2],dict(v[3])) for a,v in owner.source_masks.items()])
 decode(payload,owner.samples,identity)
 return payload

def decode(payload,samples,identity):
 if payload.get('version')!=1 or tuple(payload.get('identity',()))!=tuple(identity):raise ValueError('Source sidecar identity mismatch')
 if len(identity)!=3 or any(type(x)is not int or x<0 for x in identity) or identity[0]==0 or identity[1]>=identity[2]:raise ValueError('Invalid source interval identity')
 raw=payload['cameras']
 if type(raw)is not bytes or len(raw)!=288:raise ValueError('Invalid source camera bytes')
 c=struct.unpack('<24i24d',raw)
 if not all(math.isfinite(x) for x in c[24:]):raise ValueError('Nonfinite source camera')
 rows=payload['masks'];out={}
 if not 1<=len(rows)<=8 or len(rows)!=len(samples):raise ValueError('Invalid source mask sample count')
 for alpha,offset_bytes,mask,total,diagnostic in rows:
  if not math.isfinite(alpha) or not 0<alpha<1 or alpha not in samples or alpha in out:raise ValueError('Source mask alpha mismatch')
  scene=_decode_records(samples[alpha][0],source_keys=False);sources=scene['records'];n=len(sources)
  if scene['epoch']!=identity[0] or not identity[1]<=scene['refresh']<=identity[2]:raise ValueError('Source frame identity mismatch')
  if n>144 or type(offset_bytes)is not bytes or len(offset_bytes)!=(n+1)*4:raise ValueError('Invalid source mask offsets')
  offsets=struct.unpack('<'+'I'*(n+1),offset_bytes)
  if type(total)is not int or not 0<=total<=32768 or offsets[0]!=0 or offsets[-1]!=total or any(a>b for a,b in zip(offsets,offsets[1:])):raise ValueError('Invalid source mask extent')
  for i,source in enumerate(sources):
   faces=len(source['blocks'][5]) if source['kind']==3 else 0
   if offsets[i+1]-offsets[i]!=faces:raise ValueError('Source face topology extent mismatch')
  if type(mask)is not bytes or len(mask)!=max(1,total) or any(x>1 for x in mask):raise ValueError('Invalid source mask bits')
  if set(diagnostic)!={'rectangle_rejected_faces','selected_faces'} or any(type(v)is not int or v<0 for v in diagnostic.values()) or diagnostic['selected_faces']!=sum(mask[:total]) or diagnostic['rectangle_rejected_faces']>total:raise ValueError('Invalid source diagnostics')
  out[alpha]=((C.c_uint32*(n+1)).from_buffer_copy(offset_bytes),(C.c_uint8*max(1,total)).from_buffer_copy(mask),total,dict(diagnostic))
 return (c[:12],c[12:24],c[24:36],c[36:]),out

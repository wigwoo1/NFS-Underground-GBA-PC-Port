"""Versioned diagnostic sidecar; exact packet binding, no packet-format change."""
import hashlib,struct

def packet_layout(packet):
 h=struct.unpack_from('<8I',packet)
 if h[0]!=0x3150534e or h[2]!=len(packet) or h[3]!=5:raise ValueError('packet header')
 sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5))}
 world=struct.unpack_from('<I',sections[2],4)[0]
 order=struct.unpack_from('<'+'I'*struct.unpack_from('<I',sections[3],4)[0],sections[3],8)
 ids=[list(struct.unpack_from('<5I',sections[5],8+i*20)) for i in range(world)]
 indices=[i for i in order if i!=0xffffffff]
 if sorted(indices)!=list(range(world)):raise ValueError('draw order')
 return h,indices,ids

def build(packet,epoch,draws):
 h,indices,ids=packet_layout(packet)
 if epoch<=0 or len(draws)!=len(indices):raise ValueError('capture count/epoch')
 records=[]
 for ordinal,index in enumerate(indices):
  draw=draws[ordinal]
  if draw['ordinal']!=ordinal or draw['identity']!=ids[index]:raise ValueError('draw identity')
  records.append(dict(index=index,ordinal=ordinal,identity=ids[index],bounds=list(draw['bounds'])))
 result=dict(version=1,epoch=epoch,serial=h[4],begin=h[5],end=h[6],packet_sha256=hashlib.sha256(packet).hexdigest(),records=records)
 validate(packet,epoch,result)
 return result

def validate(packet,epoch,metadata):
 h,indices,ids=packet_layout(packet)
 if metadata['version']!=1 or metadata['epoch']!=epoch or epoch<=0 or [metadata[k] for k in ('serial','begin','end')]!=list(h[4:7]) or metadata['packet_sha256']!=hashlib.sha256(packet).hexdigest():raise ValueError('scene binding')
 if len(metadata['records'])!=len(indices):raise ValueError('record count')
 for ordinal,(index,record) in enumerate(zip(indices,metadata['records'])):
  if record['index']!=index or record['ordinal']!=ordinal or record['identity']!=ids[index]:raise ValueError('surface binding')
  bounds=record['bounds']
  if len(bounds)!=4 or any(type(v)!=int or v<0 or v>65535 for v in bounds):raise ValueError('bounds encoding')
 return True

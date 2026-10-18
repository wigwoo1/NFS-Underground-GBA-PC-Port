"""Bounded actual pending 4K readbacks, deliberately perturbs timing."""
import ctypes as C,hashlib,json,time,threading
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession']
original_prepare=Session.prepare;original_present=Session.present
folder=Path('work/camera/prototype-runs')/('ordered-tail-live-pixels-'+str(time.time_ns()));folder.mkdir()
rows=[];pending={};count=0

def prepare(self,owned,epoch,generation,index):
 global count
 result=original_prepare(self,owned,epoch,generation,index);count+=1
 if 120<=count<152:
  assert self.pending==(epoch,generation,index) and list(result['publication'][:3])==[epoch,generation,index]
  begin=time.perf_counter_ns();rgba=C.create_string_buffer(3840*2160*4);self.consumer.d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
  assert self.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  data=rgba.raw;sky=data[3840*600*4:3840*664*4];world=data[3840*1200*4:3840*1264*4]
  name=str(len(rows));(folder/(name+'.sky.rgba')).write_bytes(sky);(folder/(name+'.world.rgba')).write_bytes(world)
  draw=owned.context.draw
  row=dict(epoch=epoch,generation=generation,index=index,publication=list(result['publication']),thread=threading.get_ident(),begin_ns=begin,end_ns=time.perf_counter_ns(),width=3840,height=2160,full_sha256=hashlib.sha256(data).hexdigest(),sky_sha256=hashlib.sha256(sky).hexdigest(),world_sha256=hashlib.sha256(world).hexdigest(),sky_file=name+'.sky.rgba',world_file=name+'.world.rgba',sky_weight=draw.weight,sky_lower=hashlib.sha256(C.string_at(draw.lower,draw.skycount)).hexdigest(),sky_upper=hashlib.sha256(C.string_at(draw.upper,draw.skycount)).hexdigest(),present=None)
  rows.append(row);pending[epoch,generation,index]=row
 return result

def present(self,epoch,generation,index):
 result=original_present(self,epoch,generation,index);row=pending.pop((epoch,generation,index),None)
 if row is not None:row['present']=dict(status=result['status'],thread=threading.get_ident(),end_ns=time.perf_counter_ns())
 return result
Session.prepare=prepare;Session.present=present

def save():
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,total_prepares=count,pending=len(pending),scope='32 bounded actual pending full4K draw readbacks linked to presentation. Saved bands y600 and1200 include world/HUD overlap; no sky isolation or full fidelity/scanout/cadence proof. Readback perturbs timing.'),indent=2));print('ORDERED_TAIL_PIXEL_MANIFEST',folder/'manifest.json',flush=True)

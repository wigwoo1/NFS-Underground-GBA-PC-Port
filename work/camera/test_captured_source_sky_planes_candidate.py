import sys,json,time,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import ctypes as C,hashlib
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
from owned_native_source_sky_pan_session_candidate import NativeSourceSession
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 session=NativeSourceSession()
 import numpy as np,struct
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha];sky=asset.sample_continuous(*boundaries,alpha)
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(sky)
  source=session.source;P=C.c_void_p;source.nf_source_sky_info.argtypes=[P,P];source.nf_source_sky_copy.argtypes=[C.c_uint,P,C.c_size_t]
  assert source.nf_source_packets_begin(1,1,index)==0
  try:
   assert source.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
   flags=(C.c_uint*2)();weights=(C.c_double*2)();assert source.nf_source_sky_info(flags,weights)==0
   gn,hn,bn=struct.unpack_from('<3I',frame,8);assert hn==160*34944 and bn==76800
   palettes=np.stack([np.frombuffer(frame,dtype='<u2',count=256,offset=40+gn+y*34944+32896) for y in range(160)])
   background=np.frombuffer(frame,np.uint8,count=76800,offset=40+gn+hn);i=np.arange(38400);y=i//240
   planes=[]
   for layer in range(2):
    assert flags[layer]==(1 if layer==0 or sky.weight>0 else 0)
    if not flags[layer]:continue
    indices=background[:38400].copy() if layer==0 else np.zeros(38400,np.uint8)
    indices[10560:25696]=np.frombuffer(sky.lower if layer==0 else sky.upper,np.uint8)
    colors=palettes[y,indices];reference=np.zeros((38400,4),np.uint8)
    for channel in range(3):v=colors>>(5*channel)&31;reference[:,channel]=(v<<3)|(v>>2)
    if layer==0:reference[:,3]=background[38400:]*255
    else:
     reference[:10560]=0;reference[25696:]=0;reference[10560:25696,3]=255
    buf=C.create_string_buffer(153600);assert source.nf_source_sky_copy(layer,buf,len(buf))==0;actual=np.frombuffer(buf.raw,np.uint8).reshape(38400,4)
    assert np.array_equal(actual,reference),(index,layer,int(np.count_nonzero(actual!=reference)))
    assert weights[layer]==(1 if layer==0 else sky.weight)
    planes.append(actual.copy().reshape(160,240,4))
    results.append(dict(alpha=alpha,layer=layer,weight=weights[layer],sha256=hashlib.sha256(buf.raw).hexdigest()))
   d=session.consumer.d
   for layer,plane in enumerate(planes):assert d.nf_d3d_texture(1001+layer,240,160,plane.ctypes.data,plane.nbytes)==0
   if len(planes)==1:assert d.nf_d3d_texture(1002,240,160,planes[0].ctypes.data,planes[0].nbytes)==0;planes.append(planes[0])
   d.nf_d3d_sky_pan.argtypes=[C.c_float];assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0;assert d.nf_d3d_sky_pan(sky.weight)==0
   pixels=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(pixels,len(pixels))==0;actual=np.frombuffer(pixels.raw,np.uint8).reshape(2160,3840,4)
   u=(np.arange(3240)+.5)*2/27;v=(np.arange(2160)+.5)*2/27;x=np.floor(u).astype(int);y=np.floor(v).astype(int);shift=np.floor(u+np.float32(sky.weight))>np.floor(u)
   lower=planes[0][y[:,None],x[None,:]];upper=planes[1][y[:,None],x[None,:]];selected=np.where((shift[None,:]&(upper[:,:,3]>127))[:,:,None],upper,lower)
   reference=np.zeros((2160,3840,4),np.uint8);reference[:,:,3]=255;reference[:,300:3540]=np.where(selected[:,:,3:4]>127,selected,reference[:,300:3540]);mismatch=int(np.count_nonzero(np.any(actual!=reference,axis=2)));assert mismatch==0,('Actual source plane GPU mismatch',index,mismatch)
  finally:assert source.nf_source_packets_close()==0
finally:
 if session is not None:session.close();assert session.source.nf_owned_gpu_contexts()==0
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
out=dict(result='PASS_CAPTURED_SOURCE_SKY_PLANES',planes=results,scope='Actual native source callback planes from five complete captured scene samples match independent ROM-index/captured-frame scanline palette and coverage conversion exactly. Not live motion delivery or physical60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'])

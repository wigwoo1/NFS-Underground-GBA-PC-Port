import os,json,collections,traceback
from pathlib import Path
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'current-captured-pair','exec'))
import owned_motion_pairs as full,owned_model_key_records_candidate as model
original=full._decode_records;original_model=model._decode_records;calls=[];owners=[]
def traced(frame,*args,**kwargs):
 owners.append(frame)
 row=dict(owner_id=id(frame),frame_type=type(frame).__name__,frame_bytes=len(frame),source_keys=kwargs.get('source_keys',args[0] if args else True),callers=[dict(file=Path(x.filename).name,line=x.lineno,function=x.name) for x in traceback.extract_stack(limit=7)[:-1]])
 value=original(frame,*args,**kwargs);row['refresh']=value['refresh'];row['records']=len(value['records']);calls.append(row);return value
full._decode_records=model._decode_records=traced
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=samples=None
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 samples=ProgressiveSourceWorldSamples(prepared,(.01,.2,.4,.6,.8,.99))
 assert len(samples.samples)==6
finally:
 full._decode_records=original;model._decode_records=original_model
 if samples is not None:samples.close()
 if prepared is not None:prepared.close()
 history.close()
counts=collections.Counter(x['owner_id'] for x in calls)
out=dict(result='PASS_CURRENT_DECODE_CALLER_INVENTORY',calls=calls,unique_owners=len(counts),repeated_owner_decode_counts=[v for v in counts.values() if v>1],scope='One actual capturedpair/sixfraction preparation. Strong frame references prevent owner-id reuse during diagnostic; stack capture perturbs timings, no performance claim.')
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/current-preparation-functions-20261010')
(folder/'decode-callers.json').write_text(json.dumps(out,indent=2))
print(out['result']);print('calls',len(calls),'unique_owners',len(counts),'repeated',out['repeated_owner_decode_counts'])
print(json.dumps(collections.Counter((r['source_keys'],r['callers'][-1]['file'],r['callers'][-1]['function']) for r in calls).most_common()))

import json,sys
from pathlib import Path
from analyze_long_interval_pre_draw_candidate import audit

def analyze(r):
 prior=audit(r);rows=[]
 for e in prior['rows']:
  epoch,g,older,newer,index=e['identity']
  matches=[x for x in r['world_preparation_stage_samples'] if x['parent_sample_rows'] and x['older']==older and x['newer']==newer and x['terminal'][5]['history_identity']==[epoch,newer]];assert len(matches)==1
  x=matches[0];p=x['parent_start_timing'];w=p['input_write'];d=x['terminal'][5];s=d['sample_transfer_rows'][0];sw=s['shared_write'];q=x['parent_sample_rows'][0];sr=q['shared_read']
  points=[x['started_ns'],p['pack_begin_ns'],p['packed_ns'],w['begin_ns'],w['serialized_ns'],w['copied_ns'],w['descriptor_sent_ns'],d['child_started_ns'],d['decoded_ns'],d['initialized_ns'],d['constructed_ns'],s['ready_ns'],sw['begin_ns'],sw['serialized_ns'],sw['copied_ns'],sw['descriptor_sent_ns'],sr['begin_ns'],sr['copied_ns'],sr['decoded_ns'],q['received_ns'],q['decoded_ns'],q['publication_begin_ns'],q['published_ns']]
  assert points==sorted(points),(e['identity'],points)
  spans=[b-a for a,b in zip(points,points[1:])];assert sum(spans)==q['published_ns']-x['started_ns']
  rows.append(dict(identity=e['identity'],pipeline_ms=sum(spans)/1e6,partition_ms=[s/1e6 for s in spans]))
 return dict(result='PASS_FIRST_READY_PIPELINE_PARTITIONS',phases=['before_pack','pack','before_input_write','input_serialize','input_copy','input_descriptor','descriptor_to_child_after_receive_decode','child_decode','child_initialize','construct_sources','first_sample','before_output_write','output_serialize','output_copy','output_descriptor','parent_receive_wait','parent_private_copy','parent_shared_decode','receive_return','frame_decode','before_publish','publish'],rows=rows,scope='Monotonic elapsed stage timestamps across same-host processes, exact partition; scheduling may occur inside any stage, no exclusive CPU attribution.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

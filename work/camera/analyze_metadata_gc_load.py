import json
from pathlib import Path
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-metadata-trace-live-20261007')
r=json.loads((root/'owned-native-1791414182415415200.json').read_text());load=json.loads((root/'system-load-1791414146719952500.json').read_text())['samples'];rows=[]
for interval in r['world_preparation_stage_samples']:
 child=interval['child_stages'];gc=child.get('child_gc_rows',[])
 for sample in child.get('sample_timings',[]):
  for source in sample.get('source_sample_stages',[]):
   for anchor in source.get('anchor_stages',[]):
    for stage in anchor.get('metadata_stages',[]):
     if stage['wall_ns']<3_000_000:continue
     begin,end=stage['started_ns'],stage['completed_ns'];events=[]
     for event in gc:
      overlap=max(0,min(end,event['end_ns'])-max(begin,event['start_ns']))
      if overlap:events.append(dict(generation=event['generation'],overlap_ms=overlap/1e6,collected=event['collected'],thread_id=event['thread_id']))
     busy=[x['busy_fraction'] for x in load if x['end_ns']>begin and x['begin_ns']<end and x['busy_fraction'] is not None]
     rows.append(dict(older=interval['older'],newer=interval['newer'],alpha=sample['alpha'],stage=stage['name'],wall_ms=stage['wall_ns']/1e6,cycles=stage['thread_cycles'],gc=events,gc_overlap_ms=sum(x['overlap_ms'] for x in events),overlapping_system_busy=busy))
rows.sort(key=lambda x:x['wall_ms'],reverse=True)
(root/'metadata-gc-load.json').write_text(json.dumps(dict(result='MEASURED',outliers=rows,scope='Timestamp overlap with child GC and aggregate 250ms CPU observations. Overlap is not exclusive causal attribution; low cycle count does not certify waiting reason.'),indent=2))
(root/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(rows[:5],indent=2))
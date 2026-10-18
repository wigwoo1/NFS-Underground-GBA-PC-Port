"""Sequential same-input native route timing with complete early-work accounting."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil,csv,statistics,re
p=Path(__file__).resolve().parent;reverse='--reverse' in sys.argv
wait_comparison='--wait-comparison' in sys.argv
dirty_comparison='--dirty-comparison' in sys.argv
assert not (wait_comparison and dirty_comparison)
prefix=('layer-dirty-fullroute' if dirty_comparison else 'early-gpu-wait' if wait_comparison else 'early-gpu-fullroute')+('-reverse' if reverse else '');summary=p/(prefix+'-tests.json');runs=[]
sequence=(('dirty','normal') if reverse else ('normal','dirty')) if dirty_comparison else ((('precise','normal') if reverse else ('normal','precise')) if wait_comparison else (('early','due') if reverse else ('due','early')))
def stats(values):
 return dict(median=statistics.median(values),p95=sorted(values)[int(.95*len(values))],maximum=max(values))
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_LIVE_HUD='1',NF_LIVE_WORLD_CLASSIFIED='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_CONTINUOUS_CAMERA='1',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
summary.write_text(json.dumps(dict(result='RUNNING',runs=[])))
try:
 for mode in sequence:
  print('Starting '+mode+' full minute',flush=True);current=dict(env)
  if mode=='early' or wait_comparison or dirty_comparison:current.update(NF_PREPARATION_LEAD_US='8000',NF_PREPARE_GPU='1')
  if mode=='dirty':current['NF_LAYER_DIRTY']='1'
  if mode=='precise':current['NF_PRECISE_WAIT']='1'
  subprocess.run([sys.executable,str(p/'test_live_road_attributes.py'),'60','--window-buffer'],env=current,stdout=subprocess.DEVNULL,check=True)
  live=json.loads((p/'road-attribute-live-layer-sync-tests.json').read_text());assert live['result']=='PASS' and live['refreshes']==3583
  rows=list(csv.DictReader((p/'road-attribute-live-parity.csv').open()));log=live['host_output']
  for name in ('road-attribute-live-layer-sync-tests.json','road-attribute-live-parity.csv','road-attribute-live-parity.log'):shutil.copyfile(p/name,p/(prefix+'-'+mode+'-'+name))
  work=[(int(row['early_generation_since_display_ns'])+int(row['early_gpu_since_display_ns'])+int(row['render_end_ns'])-int(row['render_start_ns']))/1e6 for row in rows]
  total_work=sum(work)+(int(re.search(r'preparation_unreported_ns=(\d+)',log)[1])+int(re.search(r'early_gpu_unreported_ns=(\d+)',log)[1]))/1e6
  worst=[]
  for previous,row in zip(rows,rows[1:]):
   worst.append(dict(display=int(row['display_index']),swap_interval_ms=(int(row['swap_end_ns'])-int(previous['swap_end_ns']))/1e6,poll_lateness_ms=(int(row['poll_ns'])-int(row['deadline_ns']))/1e6,simulation_ms=(int(row['simulation_end_ns'])-int(row['simulation_start_ns']))/1e6,due_render_ms=(int(row['render_end_ns'])-int(row['render_start_ns']))/1e6,early_cpu_ms=int(row['early_generation_since_display_ns'])/1e6,early_gpu_consumer_ms=int(row['early_gpu_since_display_ns'])/1e6,original_steps=int(row['display_simulation_steps']),all_interval_original_steps=int(row['original_steps_since_display']),all_interval_simulation_ms=int(row['simulation_since_display_ns'])/1e6,gpu_reused=int(row['early_gpu_reused'])))
  item=dict(mode=mode,original_work_seconds=live['original_work_total_ns']/1e9,original_work_interval_ms=live['original_work_interval_ms'],host_cpu_seconds=int(re.search(r'host_cpu_ns=(\d+)',log)[1])/1e9,precise_wait=int(re.search(r'precise_wait=(\d+)',log)[1]),poll_lateness_ms=stats([(int(row['poll_ns'])-int(row['deadline_ns']))/1e6 for row in rows]),refreshes=live['refreshes'],ram_hashes=live['ram_hashes'],swap_interval_ms=live['swap_interval_ms'],skipped=sum(int(row['skipped']) for row in rows),native_frames=sum(int(row['ready']) for row in rows),early_gpu=live['early_gpu_checks'],charged_render_work_ms=stats(work),total_render_work_ms=total_work,source_delay_original_refreshes=8,worst_intervals=sorted(worst,key=lambda item:item['swap_interval_ms'],reverse=True)[:10])
  runs.append(item)
  if dirty_comparison:
   item['layer_dirty_enabled']=mode=='dirty'
   if mode=='dirty':
    clean=list(map(int,re.search(r'layer_clean_reused=(\d+) layer_clean_verified=(\d+) layer_clean_failed=(\d+)',log).groups()))
    assert clean[0]>0 and clean[1]==0 and clean[2]==0
    item['clean_pages_reused']=clean[0]
  if len(runs)>1:assert runs[0]['ram_hashes']==item['ram_hashes']
  summary.write_text(json.dumps(dict(result='RUNNING',runs=runs),indent=2));print('Completed '+mode+' with exact original state',flush=True)
 report=dict(result='PASS',wait_comparison=wait_comparison,runs=runs,host_sha256=hashlib.sha256((p/'native-endpoint-road-attributes.exe').read_bytes()).hexdigest(),bridge_sha256=hashlib.sha256((p/'visibility-probe-wide.dll').read_bytes()).hexdigest(),scope='Same original input/refresh count, sequential full-minute modes. Charged render work includes early CPU generation, early entire GPU consumer and due render once, including terminal early work; wall-time/preemption included, not exclusive CPU/GPU cost or end-to-end input latency. Fixed eight original refreshes of source delay. Process CPU seconds include current host user+kernel execution across measurement (not other processes or whole-system utilization). Wait comparison holds early rendering on in both modes and changes only precise waiting. No image readback, forced discard or profiling in either mode. Order/OS variation remains; no physical scanout or smooth60fps proof.')
except Exception as error:
 summary.write_text(json.dumps(dict(result='FAIL',error=str(error),runs=runs),indent=2));raise
report['dirty_comparison']=dirty_comparison
if dirty_comparison:report['scope']='Sequential full-minute routes: same earlyGPU, source delay8, original scripted inputs and refreshes; only renderer-write dirty tracking changes. All inherited NF flags cleared; no clean-page audit, profiling, image readback or forced discard. Complete final RAM and owned layer selection verified. Original-work wall timing includes emulation/capture/preemption, not exclusive layer cost. Prior exhaustive live clean-byte checks establish route-specific capture fidelity. No smooth60fps, physical Xbox, input latency or scanout proof.'
summary.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

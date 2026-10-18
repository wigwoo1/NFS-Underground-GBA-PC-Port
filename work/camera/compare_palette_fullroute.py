"""Sequential full-route palette modes; retain each run before next mutation."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil,csv
p=Path('work/camera').resolve();reverse='--reverse' in sys.argv[1:]
prefix='palette-fullroute-reverse' if reverse else 'palette-fullroute'
summary=p/(prefix+'-comparison-tests.json')
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_LIVE_HUD='1',NF_LIVE_WORLD_CLASSIFIED='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_CONTINUOUS_CAMERA='1',NF_CONTINUOUS_ROAD_UV='1',NF_CAPTURE_PROFILE='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
runs=[]
summary.write_text(json.dumps(dict(result='RUNNING',runs=[]),indent=2))
try:
    for mode in (('lookup','reference') if reverse else ('reference','lookup')):
        print('Starting full60second '+mode+' route',flush=True)
        args=[sys.executable,str(p/'test_live_road_attributes.py'),'60','--window-buffer']
        if mode=='reference':args.append('--reference-palette')
        subprocess.run(args,env=env,stdout=subprocess.DEVNULL,check=True)
        subprocess.run([sys.executable,str(p/'analyze_surface_capture_profile.py')],stdout=subprocess.DEVNULL,check=True)
        live=json.loads((p/'road-attribute-live-layer-sync-tests.json').read_text())
        profile=json.loads((p/'surface-capture-profile-tests.json').read_text())
        assert live['result']==profile['result']=='PASS' and live['refreshes']==3583
        for file in ('road-attribute-live-layer-sync-tests.json','surface-capture-profile-tests.json','road-attribute-live-parity.csv'):
            shutil.copyfile(p/file,p/(prefix+'-'+mode+'-'+file))
        displays=list(csv.DictReader((p/'road-attribute-live-parity.csv').open()))
        worst=[]
        for previous,row in zip(displays,displays[1:]):
            worst.append(dict(display=int(row['display_index']),swap_interval_ms=(int(row['swap_end_ns'])-int(previous['swap_end_ns']))/1e6,
                              poll_lateness_ms=(int(row['poll_ns'])-int(row['deadline_ns']))/1e6,
                              simulation_ms=(int(row['simulation_end_ns'])-int(row['simulation_start_ns']))/1e6,
                              native_generation_ms=int(row['paired_prepare_ns'])/1e6,
                              renderer_finish_ms=int(row['renderer_finish_ns'])/1e6))
        worst=sorted(worst,key=lambda item:item['swap_interval_ms'],reverse=True)[:10]
        bridge=p/('visibility-probe-wide-reference-palette.dll' if mode=='reference' else 'visibility-probe-wide.dll')
        runs.append(dict(mode=mode,bridge_sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),refreshes=live['refreshes'],ram_hashes=live['ram_hashes'],swap_interval_ms=live['swap_interval_ms'],generation_ms=live['component_ms']['paired_prepare_ns'],surface_capture=profile,worst_intervals=worst))
        if len(runs)>1:assert runs[0]['ram_hashes']==runs[-1]['ram_hashes']
        summary.write_text(json.dumps(dict(result='RUNNING',runs=runs),indent=2))
        print('Completed '+mode+' originalRAM parity and profile',flush=True)
    report=dict(result='PASS',order=[run['mode'] for run in runs],runs=runs,scope='Sequential full60second routes, same original inputs/refreshes/settings. No simultaneous builds/tests. Order/OS variation remains; timestamps include preemption and are not exclusive CPU attribution. No physical controller/scanout or smooth60fps proof.')
except Exception as error:
    summary.write_text(json.dumps(dict(result='FAIL',error=str(error),runs=runs),indent=2));raise
summary.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

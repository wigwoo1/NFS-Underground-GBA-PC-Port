"""Replay recorded per-refresh input against the preserved original bridge."""
from pathlib import Path
import ctypes as C,json,csv,hashlib,re,sys,statistics,math
manifest=Path(sys.argv[1]).resolve();session=json.loads(manifest.read_text(encoding='utf-8-sig'))
out=manifest.with_name(manifest.stem+'-verification.json')
try:
    assert session['status']=='HOST_COMPLETE' and session['exit_code']==0
    for key in ('rom','state'):
        assert hashlib.sha256(Path(session[key]).read_bytes()).hexdigest()==session[key+'_sha256'].lower(),key+' changed since recording'
    rows=list(csv.DictReader(Path(session['input_trace']).open()));assert rows,'No recorded inputs'
    log=Path(session['log']).read_text(encoding='utf-8-sig')
    def counter(key):return int(re.search(r'\b'+key+r'=(\d+)',log)[1])
    dirty_accounting=None
    if session.get('owned_submission'):
        assert counter('submission_created')>0 and counter('submission_failed')==0
    if session.get('optimized_snapshots') or re.search(r'\blayer_clean_reused=',log):
        dirty_accounting={name:counter(name) for name in ('layer_clean_reused','layer_clean_verified','layer_clean_failed')}
        assert dirty_accounting['layer_clean_failed']==0
        assert 0<=dirty_accounting['layer_clean_verified']<=dirty_accounting['layer_clean_reused']
        if session.get('optimized_snapshots'):assert dirty_accounting['layer_clean_reused']>0
    for name in ('rejected_scenes','sink_failures','paired_rejected','layer_missing','hud_failed','incompatible_scene_frames'):
        assert counter(name)==0,name+' in recorded native session'
    displays=list(csv.DictReader(Path(session['display_trace']).open()));assert displays,'Missing native presentation trace'
    ready=[row for row in displays if int(row['ready'])]
    assert ready and len(ready)==counter('rendered'), 'Native frame count mismatch'
    gpu_accounting=None
    gpu_fields=('early_gpu_since_display_ns','early_gpu_total_ns','early_gpu_reused','display_simulation_steps')
    if any(name in displays[0] for name in gpu_fields) or re.search(r'\bearly_gpu_rendered=',log):
        assert all(name in displays[0] for name in gpu_fields), 'Incomplete early GPU telemetry'
        names=('early_gpu_rendered','early_gpu_presented','early_gpu_discarded','early_gpu_pending','early_gpu_ns','early_gpu_verified','early_gpu_verification_draws','early_gpu_verify_failed','early_gpu_verified_updates','early_gpu_verification_ns')
        gpu_accounting={name:counter(name) for name in names}
        assert gpu_accounting['early_gpu_pending'] in (0,1)
        assert gpu_accounting['early_gpu_rendered']==gpu_accounting['early_gpu_presented']+gpu_accounting['early_gpu_discarded']+gpu_accounting['early_gpu_pending'], 'Early GPU lifetime mismatch'
        assert gpu_accounting['early_gpu_verify_failed']==0 and gpu_accounting['early_gpu_verified']==gpu_accounting['early_gpu_verification_draws'], 'Early image verification mismatch'
        assert gpu_accounting['early_gpu_verified_updates']>=gpu_accounting['early_gpu_verified']
        flags=[int(row['early_gpu_reused']) for row in displays]
        assert all(flag in (0,1) for flag in flags)
        assert all(not flag or int(row['ready']) for flag,row in zip(flags,displays)), 'Unavailable early frame presented'
        assert sum(flags)==gpu_accounting['early_gpu_presented'], 'Early presentation count mismatch'
        crossed=sum(flag and int(row['display_simulation_steps'])>0 for flag,row in zip(flags,displays))
        assert crossed>=gpu_accounting['early_gpu_verified'], 'Missing original-update image checks'
        previous_total=0
        for row in displays:
            total=int(row['early_gpu_total_ns']);increment=int(row['early_gpu_since_display_ns'])
            assert increment>=0 and total-previous_total==increment, 'Early GPU timing ledger mismatch'
            previous_total=total
        assert previous_total+counter('early_gpu_unreported_ns')==gpu_accounting['early_gpu_ns'], 'Unaccounted early GPU work'
        extra=gpu_accounting['early_gpu_discarded']+gpu_accounting['early_gpu_pending']+gpu_accounting['early_gpu_verification_draws']
        owned_checks=list(map(int,re.findall(r'owned_consumer_verified=(\d+)',log)))
        assert owned_checks==list(range(1,len(owned_checks)+1)), 'Owned consumer counter discontinuity'
        if owned_checks:assert len(owned_checks)==gpu_accounting['early_gpu_verified'] and session.get('owned_submission')
        extra+=len(owned_checks)
        gpu_accounting['owned_consumer_draws']=len(owned_checks)
        assert counter('hud_drawn')==len(ready)+extra, 'Native/HUD render lifetime mismatch'
        gpu_accounting['presented_after_original_updates']=crossed
    else:
        assert counter('hud_drawn')==len(ready), 'Native/HUD frame count mismatch'

    assert len(displays)==counter('swaps'), 'Presentation trace count mismatch'
    intervals=[];clock_checks=0;segments=1
    for previous,row in zip(displays,displays[1:]):
        a,b=int(previous['display_index']),int(row['display_index'])
        if b<=a:segments+=1;continue # Pause/focus/minimize restarts presentation clock.
        expected=(b-a)*16777216/(280896*60)
        assert math.isclose(float(row['target'])-float(previous['target']),expected,abs_tol=1e-8), 'Original source clock rate mismatch'
        interval=(int(row['swap_end_ns'])-int(previous['swap_end_ns']))/1e6
        assert interval>=0,'Presentation time reversed'
        intervals.append(interval);clock_checks+=1
    skipped=sum(int(row['skipped']) for row in displays)
    assert skipped==counter('skipped'), 'Skipped display count mismatch'
    assert all(int(row['epoch_mismatch'])==0 and int(row['source_older_refresh'])<=float(row['target'])<=int(row['source_newer_refresh']) for row in ready), 'Native source ownership mismatch'
    assert len(rows)==int(re.search(r'\bsimulated=(\d+)',log)[1])
    original_work_accounting=None
    fields=('simulation_since_display_ns','simulation_total_ns','original_steps_since_display','original_steps_total')
    if any(name in displays[0] for name in fields):
        assert all(name in displays[0] for name in fields), 'Incomplete original work ledger'
        previous_work=previous_steps=0
        for row in displays:
            work,steps=int(row['simulation_total_ns']),int(row['original_steps_total'])
            assert work>=previous_work and work-previous_work==int(row['simulation_since_display_ns']), 'Original work increment mismatch'
            assert steps>=previous_steps and steps-previous_steps==int(row['original_steps_since_display']), 'Original step increment mismatch'
            assert int(row['display_simulation_steps'])<=int(row['original_steps_since_display']), 'Missing due original updates'
            previous_work,previous_steps=work,steps
        assert previous_work+counter('original_work_unreported_ns')==counter('original_work_ns')
        assert previous_steps+counter('original_steps_unreported')==counter('original_steps_total')==len(rows), 'Missing original updates in ledger'
        original_work_accounting=dict(total_original_steps=previous_steps+counter('original_steps_unreported'),total_original_work_ns=counter('original_work_ns'),terminal_steps=counter('original_steps_unreported'),terminal_work_ns=counter('original_work_unreported_ns'))

    for index,row in enumerate(rows):
        assert int(row['index'])==index
        assert int(row['after'])==int(row['before'])+1
        assert 0<=int(row['keys'])<=1023
        if index:assert int(row['before'])==int(rows[index-1]['after'])
    bridge=Path(__file__).resolve().parent.parent/'nfsprobe.dll'
    d=C.CDLL(str(bridge));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
    d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
    assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
    hashes={}
    try:
        for row in rows:d.nf_frame(int(row['keys']))
        for name,address,size in (('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)):
            replay=manifest.with_name(manifest.stem+'-replay-'+name+'.bin')
            d.nf_dump(str(replay).encode(),address,size)
            actual=replay.read_bytes();recorded=Path(session['ram_prefix']+'-'+name+'.bin').read_bytes()
            assert len(actual)==len(recorded)==size and actual==recorded,name+' replay mismatch'
            hashes[name]=hashlib.sha256(actual).hexdigest()
    finally:d.nf_close()
    keys=[int(row['keys']) for row in rows]
    report=dict(result='PASS',layer_dirty_accounting=dirty_accounting,original_work_accounting=original_work_accounting,early_gpu_accounting=gpu_accounting,refreshes=len(rows),ram_hashes=hashes,input_transitions=sum(a!=b for a,b in zip(keys,keys[1:])),
                nonzero_input_refreshes=sum(bool(k) for k in keys),connected_polls=int(re.search(r'\bconnected_polls=(\d+)',log)[1]),
                recorded_epoch_count=len({row['epoch'] for row in rows}),
                native_frames=len(ready),original_source_clock_checks=clock_checks,presentation_segments=segments,
                skipped_displays=skipped,repeated_frames=counter('repeated_frames'),
                swap_interval_ms=dict(median=statistics.median(intervals),p95=sorted(intervals)[int(.95*len(intervals))],maximum=max(intervals)) if intervals else None,
                smooth_60fps_verified=False,physical_controller_verified=False,
                scope='Exact final original EWRAM/IWRAM after replaying every recorded game button mask from the preserved checkpoint. Device connection and nonzero input are telemetry, not physical Xbox control, input latency, scanout or smooth60fps proof.')
except Exception as error:
    out.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

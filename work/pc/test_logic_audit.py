"""End-to-end source cadence diagnostic; adds I/O, not a performance benchmark."""
from pathlib import Path
import argparse, csv, hashlib, json, subprocess

source = Path(__file__).resolve().parent
root = source.parent.parent
base = Path(r'C:\NFSUG-Workspace')
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', type=Path, default=base/'NFSUG-pc-cadence-audit-tests')
parser.add_argument('--direct-cached',action='store_true');parser.add_argument('--geometry-cache',action='store_true');args = parser.parse_args()
out = args.output_dir
exe = out/'NFSUG-Source-Native-Preview.exe'
rom = root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
state = root/'work/integration-0.state'
oracle = base/'NFSUG-android-capture-local/capture-off/frames.raw'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): sha(p) for p in (rom,state)}

def run(name, frames=600, extra=(), audit=True, expect_success=True):
    report=out/f'audit-{name}.json'
    log=out/f'audit-{name}.csv'
    cmd=[str(exe),'--rom',str(rom),'--state',str(state),'--hidden','--frames',str(frames),'--script','--fast','--no-audio','--oracle',str(oracle),'--report',str(report)]
    if args.geometry_cache: cmd += ['--geometry-cache']
    elif args.direct_cached: cmd += ['--direct-cached']
    if audit: cmd += ['--audit-logic',str(log)]
    cmd += list(extra)
    result=subprocess.run(cmd,timeout=90)
    r=json.loads(report.read_text())
    rows=list(csv.DictReader(log.open(newline=''))) if audit and log.exists() else []
    if expect_success:
        assert result.returncode==r['exit_code']==0,(name,r)
        assert r['logic_frames']==frames and r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==0,(name,r)
        assert r['controller_mapping_checks'] and r['render_thread_owns_gl'] and not r['full_scene_60fps']
        assert r['logic_audit_enabled']==audit and r['logic_audit_rows']==(frames if audit else 0) and not r['logic_audit_failed']
        if audit:
            assert len(rows)==frames
            assert [int(x['logic_frame']) for x in rows]==list(range(1,frames+1))
            assert all(int(x['captured'])==int(x['sky_decoded']) for x in rows)
    else:
        assert result.returncode!=0 and r['exit_code']!=0 and r['logic_frames']==0,(name,r)
    return r,rows

native, n=run('native',extra=['--audio-dump',str(out/'audit-native.pcm')])
original, o=run('original',extra=['--original','--audio-dump',str(out/'audit-original.pcm')])
assert native['native_renders']>0 and native['native_presents']>0
assert original['native_renders']==original['native_presents']==0
for a,b in zip(n,o):
    for key in ('logic_frame','segment_frame','clock_frame','original_rgba_hash','original_upper64_hash'):
        assert a[key]==b[key],(key,a,b)
assert not any(int(x['captured']) for x in o)
assert sha(out/'audit-native.pcm')==sha(out/'audit-original.pcm')=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
assert native['audio_frames']==original['audio_frames']==443007
captured=[x for x in n if int(x['captured'])]
assert len(captured)==native['published_frames']>500
# The observer publishes the last completed refresh; the core counter has advanced.
assert all(int(x['source_refresh'])+1==int(x['clock_frame']) for x in captured)
assert len({x['source_sky_rgba_hash'] for x in captured})>1

def fnv(data):
    h=14695981039346656037
    for b in data: h=((h^b)*1099511628211)&((1<<64)-1)
    return f'{h:016x}'
with oracle.open('rb') as f:
    for index in (0,60,599):
        f.seek(index*153600); image=f.read(153600)
        assert n[index]['original_rgba_hash']==fnv(image)
        assert n[index]['original_upper64_hash']==fnv(image[:240*64*4])

short,s=run('original-66',66,['--original'])
assert len(s)==66
noaudit,_=run('disabled',66,['--original'],audit=False)
gap,g=run('gap',40,['--capture-gap-at','15','--capture-gap-steps','3'])
assert not any(int(x['captured']) for x in g[14:17]) and int(g[17]['captured'])==1
reset,r=run('reset',120,['--reload-at','60'])
assert reset['reloaded'] and [int(x['segment_frame']) for x in r]==list(range(1,61))*2
assert [x['original_rgba_hash'] for x in r[:60]]==[x['original_rgba_hash'] for x in r[60:]]
toggle,t=run('toggle',120,['--toggle-at','60'])
assert toggle['toggled'] and not any(int(x['captured']) for x in t[60:])
assert any(int(x['captured']) for x in t[:60])
bad,_=run('unwritable',1,['--audit-logic',str(out/'missing-audit-parent'/'frames.csv')],audit=False,expect_success=False)
assert bad['startup_stage']=='logic audit open'
assert before=={str(p):sha(p) for p in (rom,state)}

changes=lambda rows,key: sum(a[key]!=b[key] for a,b in zip(rows,rows[1:]))
sky_changes=sum(int(a['logic_frame'])+1==int(b['logic_frame']) and a['source_sky_rgba_hash']!=b['source_sky_rgba_hash'] for a,b in zip(captured,captured[1:]))
receipt=json.loads((out/'live-build-report.json').read_text())
assert receipt['exe_sha256']==sha(exe) and receipt['core_sha256']==sha(out/'capture-host.dll')
report=dict(result='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT',frames=600,original_native_display_hashes_exact=True,oracle_hash_spot_checks=3,original_display_changes=changes(n,'original_rgba_hash'),original_upper64_changes=changes(n,'original_upper64_hash'),source_frames=len(captured),completed_source_clock_lag=1,source_sky_unique_hashes=len({x['source_sky_rgba_hash'] for x in captured}),source_sky_consecutive_changes=sky_changes,source_sky_capture_failures=600-len(captured),audio_frames=443007,audio_sha256=sha(out/'audit-native.pcm'),reset_toggle_gap_and_invalid_path_verified=True,original_mode_66_steps_verified=True,diagnostic_io_overhead=True,gpu_presentation_cadence_verified=False,full_scene_60fps=False,rom_state_unchanged=True,exe_sha256=sha(exe),core_sha256=sha(out/'capture-host.dll'),source_sha256=sha(source/'live_host.c'),test_sha256=sha(Path(__file__)))
(out/'logic-audit-test-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

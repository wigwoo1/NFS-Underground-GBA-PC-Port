from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil,argparse
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-live-host-tests';out.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
parser=argparse.ArgumentParser();parser.add_argument('--reuse-scene',action='store_true');parser.add_argument('--owned-core',action='store_true');parser.add_argument('--direct-ram-core',action='store_true');parser.add_argument('--source-transfer-core',action='store_true');parser.add_argument('--geometry-cache-core',action='store_true');parser.add_argument('--context-refresh-core',action='store_true');parser.add_argument('--output-dir',type=Path,default=out);options=parser.parse_args();out=options.output_dir;out.mkdir(exist_ok=True)
if options.source_transfer_core and (options.owned_core or options.direct_ram_core):parser.error('--source-transfer-core is a distinct verified core selection')
if options.geometry_cache_core and not options.source_transfer_core:parser.error('--geometry-cache-core requires --source-transfer-core')
if options.context_refresh_core and not options.geometry_cache_core:parser.error('--context-refresh-core requires --geometry-cache-core')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:env.pop(key,None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if '--reuse-scene' not in sys.argv:subprocess.run([sys.executable,str(source/'build_source_scene.py')],check=True,env=env)
receipt=json.loads((base/'NFSUG-pc-scene-tests/scene-build-report.json').read_text())
for name,digest in receipt['source_sha256'].items():assert sha(source/name)==digest
for name,digest in receipt['reused_camera_source_sha256'].items():assert sha(root/'work/camera'/name)==digest
units=[n for n in receipt['source_sha256'] if n.endswith('.c')]+['live_host.c','source_reader.c'];cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-mwindows']+[str(source/n) for n in units]+[str(root/'work/camera/obj_tile.c'),'-o',str(out/'NFSUG-Source-Native-Preview.exe'),'-lopengl32','-lgdi32','-luser32','-lwinmm','-lm'];subprocess.run(cmd,check=True,env=env)
core_path=base/'NFSUG-android-background-jni-native-local/capture-host.dll';core_receipt=None;parity_path=None;core_kind='normal'
if options.owned_core or options.direct_ram_core:
 experiment=base/'NFSUG-pc-owned-assembly-core-tests';parity_path=experiment/'owned-core-test-report.json';core_receipt=json.loads(parity_path.read_text());assert core_receipt['result']=='PASS_OWNED_ASSEMBLY_CORE_PARITY' and core_receipt['core_sha256']==sha(experiment/'capture-host.dll') and core_receipt['baseline_core_sha256']==sha(core_path);core_path=experiment/'capture-host.dll';core_kind='owned-assembly'
if options.direct_ram_core:
 experiment=base/'NFSUG-pc-direct-ram-core-tests';parity_path=experiment/'owned-core-test-report.json';core_receipt=json.loads(parity_path.read_text());assert core_receipt['result']=='PASS_OWNED_ASSEMBLY_CORE_PARITY' and core_receipt['all_complete_source_bytes_exact'] and core_receipt['core_sha256']==sha(experiment/'capture-host.dll') and core_receipt['baseline_core_sha256']==sha(core_path) and core_receipt['build_report_sha256']==sha(experiment/'owned-core-build-report.json');core_path=experiment/'capture-host.dll';core_kind='owned-assembly-direct-ram'
if options.source_transfer_core:
 experiment=base/'NFSUG-pc-source-transfer-core';parity_path=experiment/'source-transfer-core-test-report.json';core_receipt=json.loads(parity_path.read_text());factory=json.loads((experiment/'source-transfer-build-report.json').read_text())
 assert core_receipt['result']=='PASS_SOURCE_TRANSFER_CORE_PARITY' and core_receipt['all_complete_source_bytes_exact'] and core_receipt['all_transferred_allocations_released_after_core_close']
 assert core_receipt['core_sha256']==factory['core_sha256']==sha(experiment/'capture-host.dll') and core_receipt['maintained_build_receipt_sha256']==sha(experiment/'source-transfer-build-report.json')
 for n,h in core_receipt['source_sha256'].items():assert sha(source/n)==h,n
 assert core_receipt['maintained_test_sha256']==sha(source/'test_source_transfer_core.py')
 assert factory['abi_source_sha256']=={n:sha(source/n) for n in ['source_transfer_observer.inc','source_transfer_core_api.inc']}
 core_path=experiment/'capture-host.dll';core_kind='maintained-source-transfer'
if options.geometry_cache_core:
 experiment=base/'NFSUG-pc-geometry-cache-core';parity_path=experiment/'geometry-cache-core-test-report.json';core_receipt=json.loads(parity_path.read_text());factory=json.loads((experiment/'geometry-cache-build-report.json').read_text())
 assert core_receipt['result']=='PASS_GUARDED_GEOMETRY_CACHE_CORE_PARITY' and core_receipt['all_complete_source_bytes_exact'] and core_receipt['all_transferred_allocations_released_after_core_close'] and core_receipt['mutable_outcome_changes_force_misses'] and core_receipt['expired_geometry_owner_rejected']
 assert core_receipt['baseline_core_sha256']==sha(core_path) and core_receipt['core_sha256']==factory['core_sha256']==sha(experiment/'capture-host.dll') and core_receipt['build_receipt_sha256']==sha(experiment/'geometry-cache-build-report.json')
 for n,h in core_receipt['maintained_source_sha256'].items():assert sha(source/n)==h,n
 assert core_receipt['maintained_test_sha256']==sha(source/'test_geometry_cache_core.py') and factory['script_sha256']==sha(source/'build_geometry_cache_core.py')
 core_path=experiment/'capture-host.dll';core_kind='optional-guarded-geometry-cache'
if options.context_refresh_core:
 diagnostic=base/'NFSUG-pc-scene-rejection-core';dr=json.loads((diagnostic/'scene-rejection-core-test-report.json').read_text())
 assert dr['result']=='PASS_READONLY_SCENE_REJECTION_CORE_PARITY' and dr['all_complete_source_bytes_exact'] and dr['baseline_core_sha256']==sha(core_path) and dr['core_sha256']==sha(diagnostic/'capture-host.dll')
 experiment=base/'NFSUG-pc-model-context-handoff';parity_path=experiment/'context-refresh-core-test-report.json';core_receipt=json.loads(parity_path.read_text());factory=json.loads((experiment/'context-refresh-build-report.json').read_text());proof=json.loads((experiment/'probe/context-refresh-probe-report.json').read_text())
 assert core_receipt['result']=='PASS_CONTEXT_REFRESH_HANDOFF_CORE_PARITY' and core_receipt['all_complete_source_bytes_exact'] and core_receipt['transfers_balanced'] and core_receipt['baseline_core_sha256']==dr['core_sha256']
 assert core_receipt['core_sha256']==factory['core_sha256']==proof['core_sha256']==sha(experiment/'capture-host.dll') and core_receipt['build_report_sha256']==sha(experiment/'owned-core-build-report.json')
 assert proof['result']=='PASS_CONTEXT_HANDOFF_RECOVERS_SCENE_458' and proof['build_receipt_sha256']==sha(experiment/'context-refresh-build-report.json') and factory['handoff_enabled']
 for n,h in core_receipt['maintained_source_sha256'].items():assert sha(source/n)==h,n
 assert core_receipt['maintained_test_sha256']==sha(source/'test_model_context_core.py') and proof['maintained_probe_sha256']==sha(source/'probe_model_context_refresh.py') and factory['script_sha256']==sha(source/'build_model_context_refresh_core.py')
 core_path=experiment/'capture-host.dll';core_kind='guarded-model-context-refresh'
shutil.copy2(core_path,out/'capture-host.dll');shutil.copy2(Path('C:/msys64/mingw64/bin/libgcc_s_seh-1.dll'),out/'libgcc_s_seh-1.dll');shutil.copy2(Path('C:/msys64/mingw64/bin/libwinpthread-1.dll'),out/'libwinpthread-1.dll')
b=dict(core_kind=core_kind,capture_mode_flags=['--geometry-cache'] if options.geometry_cache_core else ['--direct-cached'] if options.source_transfer_core else [],core_factory_receipt_sha256=sha(base/'NFSUG-pc-model-context-handoff/context-refresh-build-report.json') if options.context_refresh_core else sha(base/'NFSUG-pc-geometry-cache-core/geometry-cache-build-report.json') if options.geometry_cache_core else sha(base/'NFSUG-pc-source-transfer-core/source-transfer-build-report.json') if options.source_transfer_core else None,core_parity_receipt_sha256=sha(parity_path) if parity_path else None,result='BUILT_LIVE_HOST_TESTS_PENDING',command=cmd,source_sha256={n:sha(source/n) for n in list(receipt['source_sha256'])+['live_host.c','source_reader.c','source_reader.h','build_live_host.py']},controller_sha256=sha(root/'outputs/nfsug-research/controller.h'),scene_receipt_sha256=sha(base/'NFSUG-pc-scene-tests/scene-build-report.json'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=sha(out/'capture-host.dll'),runtime_sha256=sha(out/'libgcc_s_seh-1.dll'),pthread_sha256=sha(out/'libwinpthread-1.dll'),live_readback=False,full_scene_60fps=False)
(out/'live-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','source_sha256']},indent=2))

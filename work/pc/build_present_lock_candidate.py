from pathlib import Path
import hashlib,json,os,shutil,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-lock-tests';parent=base/'NFSUG-pc-swap-observation-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((parent/'live-build-report.json').read_text())
for name,digest in receipt['source_sha256'].items():
 if name!='live_host.c':assert sha(source/name)==digest,name
assert receipt['core_sha256']==sha(parent/'capture-host.dll')
command=list(receipt['command']);command[command.index('-o')+1]=str(out/'NFSUG-Source-Native-Preview.exe')
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');run=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90);(out/'host-build.log').write_text(run.stdout+run.stderr,encoding='utf-8');run.check_returncode()
shutil.copyfile(parent/'capture-host.dll',out/'capture-host.dll');receipt.update(command=command,exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_kind='guarded-traffic-refresh2-present-lock-candidate',publication_lock_split=True,live_integration_verified=False,builder_sha256=sha(Path(__file__)));receipt['source_sha256']['live_host.c']=sha(source/'live_host.c')
(out/'live-build-report.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(dict(result='PASS_PRESENT_LOCK_HOST_BUILD',exe_sha256=receipt['exe_sha256'],core_sha256=receipt['core_sha256']),indent=2))

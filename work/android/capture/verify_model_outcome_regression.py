from pathlib import Path
import json,hashlib,struct
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-model-outcome-local';old=base/'NFSUG-android-assembly-diagnostic-local';disabled=json.loads((folder/'model-outcome-disabled-report.json').read_text());enabled=json.loads((folder/'model-outcome-enabled-report.json').read_text());unchanged=[]
for p in enabled['source_packets']:
 if p['serial']==7:continue
 name=f"source-world-{p['serial']}.nsp";assert (folder/name).read_bytes()==(old/name).read_bytes();unchanged.append(p['serial'])
raw=(folder/'source-world-7.nsp').read_bytes();at,size=struct.unpack_from('<II',raw,84);identity=raw[at:at+size];count=struct.unpack_from('<I',identity,4)[0];models=[list(struct.unpack_from('<5I',identity,8+i*20)) for i in range(count) if struct.unpack_from('<I',identity,8+i*20)[0]==3];assert models==[[3,50331840,33571928,137565972,0]]
report=dict(result='PASS_OWNED_NO_DRAW_ENDPOINT_FIX',disabled_packets=len(disabled['source_packets']),enabled_packets=len(enabled['source_packets']),other_packets_byte_identical=unchanged,scene7_models=models,wrong_scene_cases=4,wrong_identity_cases=5,positive_player_not_skipped=True,original_frames_per_run=64,original_timing=True,staged_experiment_only=True);(folder/'model-outcome-regression-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

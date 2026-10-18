from pathlib import Path
import collections,hashlib,json,struct
base=Path('C:/NFSUG-Workspace');folder=base/'NFSUG-exact-wall-replay-fixtures';old=base/'NFSUG-restored-composition-fixtures';gpu=base/'NFSUG-android-local/app-restored-composition-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());records={r['owner']['serial']:r for r in capture['road_records']};hardware=json.loads((gpu/'original-hardware-wall-audit.json').read_text());matched=[]
actual=json.loads((base/'NFSUG-wall-span-trace-fixtures/original-wall-address-report.json').read_text());actual_writers={(p['owner_serial'],p['x'],p['y']):p['original_span_refresh'] for p in actual['points']}
for point in hardware['source_points']:
 r=records[point['owner_serial']];page=(folder/r['full_replay']['filename']).read_bytes();proof=(folder/r['provenance']['filename']).read_bytes();cell=point['y']*240+point['x'];value=page[cell];writer=struct.unpack_from('<I',proof,38400+cell*4)[0];matched.append(value==point['original_hardware_index']);assert proof[cell]==2 and value==point['original_hardware_index'] and writer==actual_writers[(point['owner_serial'],point['x'],point['y'])],(point,value,writer)
wall_checks=0;mismatches=[];same_nrb=0
for entry in capture['fixtures'].values():
 raw=(folder/entry['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['background_bundle_sha256'];same_nrb+=raw==(old/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);layer=nab[nh[12]:nh[12]+nh[13]]
 for y in range(160):
  owner=entry['owners'][int(h[5]==2 and y>=h[6])];record=records[owner['serial']];proof=(folder/record['provenance']['filename']).read_bytes();page=(folder/record['full_replay']['filename']).read_bytes()
  for x in range(240):
   cell=y*240+x
   if proof[cell]!=2:continue
   offset=owner['page']*0xa000+cell;part,within=divmod(offset,4096);ref=struct.unpack_from('<H',layer,20512+(y*25+part)*2)[0];original=layer[28512+ref*4096+within];wall_checks+=1
   if page[cell]!=original:mismatches.append((entry['refresh'],owner['serial'],x,y,page[cell],original))
covered_background_checks=0;unowned_background_changes=0;unchanged_sky=0
for entry in capture['fixtures'].values():
 new=(folder/entry['filename']).read_bytes();prior=(old/entry['filename']).read_bytes();nh=struct.unpack_from('<16Q',new);oh=struct.unpack_from('<16Q',prior)
 assert nh[3:8]==oh[3:8];unchanged_sky+=new[nh[8]:nh[8]+nh[9]]==prior[oh[8]:oh[8]+oh[9]]
 for owner in range(nh[7]):
  bg=new[nh[10+owner*2]:nh[10+owner*2]+76880];before=prior[oh[10+owner*2]:oh[10+owner*2]+76880];assert bg[:80]==before[:80] and bg[38480:]==before[38480:]
  for cell in range(38400):
   if bg[38480+cell]:assert bg[80+cell]==before[80+cell];covered_background_checks+=1
   elif bg[80+cell]!=before[80+cell]:unowned_background_changes+=1
assert unchanged_sky==9 and not mismatches and len(matched)==88 and wall_checks>200000
mode=json.loads((folder/'exact-wall-mode-report.json').read_text());assert mode['failed']==0 and mode['shaded_spans']>0
on=json.loads((base/'NFSUG-android-exact-wall-replay-local/600-frame-audit/enabled-report.json').read_text());reference=json.loads((base/'NFSUG-android-shared-outcome-local/600-frame-audit/enabled-report.json').read_text());assert on['source_packets']==reference['source_packets'] and on['failure_stages']=={}
report=dict(result='PASS_EXACT_ORIGINAL_WALL_REPLAY_HARDWARE',mode=mode,original_frames=600,original_timing=True,audio_frames=capture['audio_frames'],audio_sha256=capture['audio_sha256'],formerly_uncovered_hardware_indices_matched=sum(matched),unchanged_background_scene_bundles=same_nrb,unchanged_sky_source_bundles=unchanged_sky,covered_background_indices_unchanged=covered_background_checks,changed_unowned_background_indices=unowned_background_changes,default_source_endpoint_packets_unchanged=len(on['source_packets']),wall_hardware_checks=wall_checks,wall_hardware_mismatches=len(mismatches),mismatch_examples=mismatches[:20],gpu_rendering_tested=False)
native=base/'NFSUG-android-exact-wall-native-local';build=json.loads((native/'capture-jni-build-report.json').read_text());assert build['jni'] and build['visibility_capacity']==64
for cache in (base/'NFSUG-android-exact-wall-replay-local',native):
 provenance=json.loads((cache/'source-provenance.json').read_text())
 for name in ('camera/world_trace.h','camera/native_wall.c','camera/native_scene_executor.c','camera/native_scene_executor.h'):
  assert hashlib.sha256((Path('Y:/CODEX/NFSUG-Native-PC-Port/work')/name).read_bytes()).hexdigest()==provenance['unaltered_source_sha256'][name]
assert {r['abi'] for r in build['targets']}=={'x86_64','arm64-v8a'}
for target in build['targets']:assert not target['legacy_speed_apis_exported'] and min(target['load_alignments'])>=16384
report['actual_original_wall_writer_frames_matched']=88;report['android_build_targets']=build['targets'];report['canonical_source_hashes_verified']=True;report['android_runtime_verified']=False
(folder/'exact-wall-hardware-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

from pathlib import Path
import hashlib,json
base=Path(r'C:\NFSUG-Workspace\NFSUG-Android-Native-Wide-20261017');folder=base/'rejection-probe-results'
p=folder/'rejection-probe-report.json';r=json.loads(p.read_text());v=r['step518']['capture_context']['packet_rejection'];assert len(v)==153 and v[:2]==[0x3152504e,1]
assert v[2:6]==r['step518']['timing'] and v[6:14]==r['step518']['capture_stats']
detail,bad,model,visits=v[14:23],v[23:32],v[32:40],v[40:153]
assert detail==[114,12355,12359,0,1,14,16,2,0]
assert bad[0]==0x03004770 and bad[1]==1 and bad[5]==0x03007dc8
assert model==[114,12359,0x0200c36c,4,1,0x03007dc8,0x03007dc8,0]
assert visits[0]==3
draws=[visits[1+i*7:8+i*7] for i in range(visits[0])]
assert [x[5:] for x in draws]==[[1,1],[1,1],[0,1]]
assert draws[2][0]==12359 and draws[2][2]==0x02004458
assert model[1]-model[3]>=detail[1]
previous=json.loads((base/'background-probe-results/background-probe-report.json').read_text())
assert r['original']==previous['original'] and r['native']==previous['native']
assert r['step518']['capture_context']['background_probe']==previous['step518']['capture_context']['background_probe']
assert r['frozen_component_sha256']==previous['frozen_component_sha256']
report=dict(result='VERIFIED_SCENE114_REJECTED_THIRD_MODEL_CAPTURE_NULL',epoch=2,rejected_serial=114,begin_refresh=12355,end_refresh=12359,page=0,assembly_failed=True,recorded_surface_count=14,recorded_commands=16,recorded_models=2,first_bad_guest_pc='0x03004770',first_bad_registers=bad[1:],model_rejection_detail=model,model_draw_visits=draws,failed_model_object='0x02004458',rotation_address='0x0200c36c',rotation_age_refreshes=4,rotation_found_in_scene_interval=True,context_match=True,model_capture_present=False,exact_inner_failure_reason_established=False,original_pixels_pcm_clocks_exact=True,background_query_and_provenance_exact_to_prior_probe=True,production_fix=False,full_scene_60fps=False,report_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),next_dependency='Distinguish live_native_model_assemble context identity, immutable owned-model ready/epoch/args/rotation guard and nf_extract_model result at scene114 final model. A matching rotation record does not prove exact immutable source inputs. Do not bypass ownership or omit model.')
(folder/'packet-rejection-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

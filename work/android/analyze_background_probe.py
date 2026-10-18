from pathlib import Path
import hashlib,json,struct
base=Path(r'C:\NFSUG-Workspace\NFSUG-Android-Native-Wide-20261017');folder=base/'background-probe-results'
r=json.loads((folder/'background-probe-report.json').read_text());w=r['step518'];v=w['capture_context']['background_probe']
assert len(v)==64 and v[0]==0x3147424e and v[1]==1 and v[2:6]==v[52:56]==[16777216,280896,12360,518]
assert v[6]==1 and v[7:12]==[2,12359,5,4,1] and v[12:14]==[2,12359]
assert v[14]==v[23]==v[36]==0 and v[45]==5312 and v[46:52]==[0]*6
p=folder/'background-provenance.bin';raw=p.read_bytes();words=struct.unpack('<664Q',raw)
assert words[:8]==(2,12359,5,4,1,3,160,1)
owners=[list(words[8:16]),list(words[16:24])];assert owners==[[2,112,12345,12350,0,4025920,3,1],[2,113,12350,12355,1,4058340,3,1]]
rows=[words[24+y*4:28+y*4] for y in range(160)]
runs=[]
for y,row in enumerate(rows):
    page=(row[0]>>4)&1
    if runs and runs[-1]['page']==page:runs[-1]['last_row']=y
    else:runs.append(dict(first_row=y,last_row=y,page=page))
assert runs==[dict(first_row=0,last_row=118,page=1),dict(first_row=119,last_row=159,page=0)]
assert all(row[3]==3 for row in rows)
assert all(rows[y][2]==owners[1][5] for y in range(119))
assert all(rows[y][1]!=owners[0][5] for y in range(119,160))
assert set(rows[y][1] for y in range(119,160))=={4096864}
report=dict(result='VERIFIED_LAYER_CONTEXT_PRESENT_OWNER_JOIN_UNAVAILABLE_AT518',step=518,refresh=12359,epoch=2,layer_info_present=True,whole_pair_available=False,split_available=False,display_owner_available=False,provenance_bytes=5312,bundle_bytes=0,background_bytes=0,retained_owners=owners,displayed_page_runs=runs,page1_rows_match_retained_owner113=True,page0_rows=41,page0_displayed_generation=4096864,page0_retained_owner112_generation=4025920,read_only_original_pixels_pcm_clocks_exact=True,production_fix=False,full_scene_60fps=False,provenance_sha256=hashlib.sha256(raw).hexdigest(),report_sha256=hashlib.sha256((folder/'background-probe-report.json').read_bytes()).hexdigest(),next_dependency='Observe the native packet capture rejection preceding refresh12359; retained owners112/113 do not cover the newer displayed page0 generation. Missing owner identity/rejection reason not yet established. Preserve strict ownership checks.',schema=dict(magic=0,version=1,timing_before=[2,6],layer_ok=6,layer_info=[7,12],query_epoch=12,query_refresh=13,pair_ok=14,pair=[15,23],split_ok=23,split=[24,36],display_owner_ok=36,display_owner=[37,45],provenance_bytes=45,bundle_bytes=46,sky_bytes=47,sky_scene_bytes=48,background_bytes=49,layer_query_bundle_bytes=50,layer_query_background_bytes=51,timing_after=[52,56],stats_after=[56,64]))
(folder/'background-probe-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:x for k,x in report.items() if k!='schema'},indent=2))

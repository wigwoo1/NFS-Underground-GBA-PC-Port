from pathlib import Path
import ctypes as C,json,sys
p=Path('work/camera');native=C.CDLL(str((p/'road-pair-uv.dll').resolve())).nf_road_pair_uv;native.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];tested=0
s=(p/'sample_original_write_order_oracle.py').read_text();begin=s.index('# Independent diagnostic oracle.');end=s.index("for road,g in zip(r['checks'],geo['roads']):",begin);s=s[:begin]+s[end:];s=s.replace('stable-road-owned-continuous-clipped-rings.json','world-source-clipped-rings.json');s=s.replace('stable-road-original-write-order-oracle-','native-road-pair-uv-pixels-');s=s.replace("  uv=[fixed[k]/", "  native_out=(C.c_int32*2)();assert all(v==int(v) for v in a[1:]+b[1:]);assert native((C.c_int32*3)(*map(int,a[1:])),(C.c_int32*3)(*map(int,b[1:])),width,pair,table,native_out);assert list(native_out)==fixed,(list(native_out),fixed,width,pair);tested+=1\n  uv=[native_out[k]/")
sys.argv=['pair_uv','1'];exec(compile(s,'native_pair_differential','exec'),globals());out=(C.c_int32*2)(77,88);assert not native((C.c_int32*3)(0,0,-1),(C.c_int32*3)(0,0,1),10,0,table,out);assert list(out)==[77,88]
guard_checks=0
for width,pair,a,b in [(0,0,(0,0,64),(0,0,64)),(32768,0,(0,0,64),(0,0,64)),(10,10,(0,0,64),(0,0,64)),(64,63,(0,0,64),(0,0,-4096))]:
 out=(C.c_int32*2)(77,88);assert not native((C.c_int32*3)(*a),(C.c_int32*3)(*b),width,pair,table,out);assert list(out)==[77,88];guard_checks+=1
report=dict(result='PASS',atomic_boundary_rejections=guard_checks,exact_pair_uv_checks=tested,all_original_pixel_indices_exact=True,atomic_invalid_q=True,scope='Integer endpoint evaluator, no fractional attribute/GPU integration or full motion proof.');(p/'native-road-pair-uv-tests.json').write_text(json.dumps(report,indent=2));print(report)

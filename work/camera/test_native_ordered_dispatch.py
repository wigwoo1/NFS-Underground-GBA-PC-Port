from pathlib import Path
import ctypes as C,json
p=Path('work/camera');r=json.loads((p/'texture-provenance-tests.json').read_text())
d=C.CDLL(str((p/'ordered-dispatch-test.dll').resolve()))
f=d.nf_ordered_dispatch;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
checks=0
for scene in r['dispatch_samples']:
    commands=scene['commands'];passes=scene['wall_passes'];n=len(commands)
    c=(C.c_uint32*(n*6))(*(v for row in commands for v in row))
    wp=(C.c_uint32*(n*3))(*(v for row in passes for v in (row or [0,0,0])))
    rows=[[i,row[2],int(bool(passes[i][1])),row[5]] for i,row in enumerate(commands) if row[0]==2]
    def pack(rows):return (C.c_uint32*(len(rows)*4))(*(v for row in rows for v in row))
    out=(C.c_uint32*258)()
    assert f(c,n,wp,pack(rows),len(rows),out)
    assert out[0]==n and list(out[1:n+1])==list(range(n)) and not any(out[n+1:])
    subset=rows[1:]
    assert f(c,n,wp,pack(subset),len(subset),out)
    assert list(out[1:out[0]+1])==[i for i in range(n) if i!=rows[0][0]]
    for field,value in [(0,n),(1,0),(2,2),(3,2)]:
        bad=[row[:] for row in rows];bad[0][field]=value
        C.memset(out,0xa5,C.sizeof(out));before=bytes(out)
        assert not f(c,n,wp,pack(bad),len(bad),out) and bytes(out)==before
        checks+=1
    bad=rows+[rows[0]]
    assert not f(c,n,wp,pack(bad),len(bad),out) and bytes(out)==before
    checks+=1
report=dict(result='PASS',scenes=206,atomic_rejections=checks,scope='Native retained-occurrence selection component; captured inputs. Not live integration, candidate insertion or cross-scene identity.')
(p/'native-ordered-dispatch-tests.json').write_text(json.dumps(report,indent=2));print(report)

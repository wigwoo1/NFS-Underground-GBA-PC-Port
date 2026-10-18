"""Independent original bridge RAM replay of a continuous native input ledger."""
from pathlib import Path
import ctypes as C,json,hashlib,sys
p=Path('work/camera').resolve();report_path=Path(sys.argv[1]);r=json.loads(report_path.read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'race.state';dll=p.parent/'nfsprobe.dll'
protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state,dll)}
d=C.CDLL(str(dll));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
ledger=r['startup_inputs']+r['inputs'];assert ledger
assert all(b['refresh']==a['refresh']+1 for a,b in zip(ledger,ledger[1:])), 'Nonconsecutive original refresh ledger'
checks=[]
try:
 for row in ledger:d.nf_frame(row['keys'])
 for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  expected=r['final_ram'][name];target=report_path.with_suffix('.original-'+name+'.bin');d.nf_dump(str(target).encode(),address,n)
  a=Path(expected['path']).read_bytes();b=target.read_bytes();assert len(a)==len(b)==n and a==b,name
  assert hashlib.sha256(a).hexdigest()==expected['sha256'];checks.append(dict(region=name,bytes=n,exact=True))
finally:d.nf_close()
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
result=dict(result='PASS_CONTINUOUS_NATIVE_ORIGINAL_RAM',startup_updates=len(r['startup_inputs']),live_updates=len(r['inputs']),native_scenes=r['owned_scene_submissions'],checks=checks,scope='Independent untouched nfsprobe replay with no native source hooks. Exact complete EWRAM/IWRAM proves recorded game-state preservation; not physical inputs or60fps proof.')
report_path.with_suffix('.verification.json').write_text(json.dumps(result,indent=2));print(result)

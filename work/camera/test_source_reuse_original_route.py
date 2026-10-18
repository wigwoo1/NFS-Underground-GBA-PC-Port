"""Verify reused surface/road construction on original route including multipass boundaries."""
from pathlib import Path
p=Path(__file__).resolve().parent
source=(p/'test_live_owned_indexed_copy.py').read_text()
needle="assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)"
assert source.count(needle)==1
source=source.replace(needle,"assert crt._putenv_s(b'NF_TEST_SURFACE_COMMAND_REUSE_VERIFY',b'1')==0\nassert crt._putenv_s(b'NF_TEST_ROAD_COMMAND_REUSE_VERIFY',b'1')==0\n"+needle)
source=source.replace("p/'live-owned-indexed-copy-tests.json'","p/'source-reuse-original-route-tests.json'")
exec(compile(source,str(p/'test_live_owned_indexed_copy.py'),'exec'))

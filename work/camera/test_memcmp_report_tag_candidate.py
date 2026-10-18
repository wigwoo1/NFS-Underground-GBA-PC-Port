import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import run_native_d3d_texture_backdrop_memcmp_candidate as runner
reported=r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\camera\prototype-runs\owned-native-1791684131132207000.json'
assert str(runner.report_path_from_output('startup log\n'+reported+'\n{result: SMOKE_COMPLETE}\n'))==reported
try:runner.report_path_from_output('no report path\n')
except RuntimeError:pass
else:raise AssertionError('missing path was not rejected')
p=Path.cwd()/'.texture-cache-tag-test.json'
assert not p.exists()
try:
 p.write_text(json.dumps({'result':'SMOKE_COMPLETE'}))
 row=runner.tag_report(p)
 reread=json.loads(p.read_text())
 assert row==reread and reread['texture_cache_variant']==runner.VARIANT
 assert reread['texture_cache_variant_source']==runner.SOURCE.name
 assert len(reread['texture_cache_variant_source_sha256'])==64
 print('PASS candidate report path extraction and identity/hash tagging:',reread['texture_cache_variant'],reread['texture_cache_variant_source_sha256'])
finally:
 if p.exists():p.unlink()
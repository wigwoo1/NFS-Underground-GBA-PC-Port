import hashlib,io,json,re,runpy,sys
from contextlib import redirect_stdout
from pathlib import Path
import owned_native_source_texture_backdrop_session_candidate as session
from owned_source_d3d_texture_backdrop_consumer_memcmp_candidate import OwnedD3DConsumer
session.OwnedD3DConsumer=OwnedD3DConsumer
VARIANT='exact_bytes_memcmp_v1'
SOURCE=Path(__file__).with_name('owned_source_d3d_texture_backdrop_consumer_memcmp_candidate.py')
def tag_report(path):
 p=Path(path);data=json.loads(p.read_text())
 data['texture_cache_variant']=VARIANT
 data['texture_cache_variant_source_sha256']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 data['texture_cache_variant_source']=SOURCE.name
 p.write_text(json.dumps(data,indent=2))
 return data
def report_path_from_output(output):
 matches=re.findall(r'(?m)^([A-Za-z]:\\.*\.json)$',output)
 if not matches:raise RuntimeError('could not identify generated run report for candidate tagging')
 return Path(matches[-1])
if __name__=='__main__':
 captured=io.StringIO()
 with redirect_stdout(captured):
  runpy.run_path('work/camera/run_native_d3d_texture_backdrop_candidate.py',run_name='__main__')
 output=captured.getvalue();sys.stdout.write(output)
 report=report_path_from_output(output);data=tag_report(report)
 print({'tagged_report':str(report),'texture_cache_variant':data['texture_cache_variant'],'texture_cache_variant_source_sha256':data['texture_cache_variant_source_sha256']})
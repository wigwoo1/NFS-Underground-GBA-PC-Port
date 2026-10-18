"""Isolated endpoint owner substage trace, same original function decisions."""
import sys
from pathlib import Path
import owned_model_record_owners as original
reference=original.model_record_owners
source=Path(original.__file__).read_text()
needle='visits=ordinary_model_visits(scene,pair.portal.sample(endpoint));frame='
assert source.count(needle)==1
source=source.replace(needle,"visits=ordinary_model_visits(scene,pair.portal.sample(endpoint));stage('ordinary_visits_'+str(endpoint));frame=")
needle='  endpoint_external.append(external_map)'
assert source.count(needle)==1
source=source.replace(needle,"  stage('external_ownership_'+str(endpoint))\n"+needle)
namespace=dict(__file__=original.__file__)
exec(compile(source,'endpoint_owner_phases','exec'),namespace)
fn=namespace['model_record_owners']
def install():
 for name,module in list(sys.modules.items()):
  if name.startswith(('owned_','sample_')) and getattr(module,'model_record_owners',None) is reference:module.model_record_owners=fn
 original.model_record_owners=fn

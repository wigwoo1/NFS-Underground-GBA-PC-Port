from functools import lru_cache
from types import ModuleType
import sys
from owned_cache_diagnostics import snapshot
m=ModuleType('owned_diagnostic_fixture')
@lru_cache(maxsize=2)
def value(x):return x*2
m.value=value;m.alias=value;sys.modules[m.__name__]=m
try:
 value(1);value(1);value(2)
 before=value.cache_info();rows=snapshot();after=value.cache_info()
 assert before==after
 names=[k for k in rows if k.startswith(m.__name__+'.')];assert len(names)==1
 assert rows[names[0]]==dict(hits=1,misses=2,maxsize=2,currsize=2)
 assert snapshot()==rows and value.cache_info()==before
finally:sys.modules.pop(m.__name__)
print('PASS: read-only counters, alias deduplication, bounded size and stable repeated snapshot')

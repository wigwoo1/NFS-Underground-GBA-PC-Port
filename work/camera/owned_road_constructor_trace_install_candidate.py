"""Optional breakdown of existing road constructor; no source logic replacement."""
import inspect,textwrap,time
from owned_thread_cycles import read
from owned_sampled_road_sequence import SampledRoadSequence
original=SampledRoadSequence.__init__
s=textwrap.dedent(inspect.getsource(original))
s=s.replace(' groups={}'," self.constructor_stages=[];_begin=time.perf_counter_ns();_cycles=read()\n def _stage(name):\n  nonlocal _begin,_cycles\n  end=time.perf_counter_ns();cycles=read();self.constructor_stages.append(dict(name=name,started_ns=_begin,completed_ns=end,wall_ns=end-_begin,thread_cycles=cycles-_cycles));_begin=end;_cycles=cycles\n groups={}")
for needle,name in [(' # Original region_setup','index_and_topology'),(' self._records=OrderedDict()','hidden_child_validation'),(' visited={','record_cache_setup'),(' self._decoded_sources={}','eager_record_encoding')]:
 assert s.count(needle)==1
 s=s.replace(needle," _stage("+repr(name)+")\n"+needle)
needle=' for source in self.sources:\n  if source.descriptor in visited'
assert s.count(needle)==1
s=s.replace(needle," _stage('endpoint_visibility')\n"+needle)
ns=dict(original.__globals__,read=read);exec(compile(s,'road-constructor-phase-trace','exec'),ns);SampledRoadSequence.__init__=ns['__init__']

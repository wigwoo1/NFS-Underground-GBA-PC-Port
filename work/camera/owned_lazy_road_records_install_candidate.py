"""Validate eager endpoint records, encode bytes on first actual use."""
import inspect,textwrap
from owned_complete_road_gpu import validate_road_record
from owned_sampled_road_sequence import SampledRoadSequence
original=SampledRoadSequence.__init__
stats=dict(validations=0)
installed=False
def validate(context,source,bounds):
 stats['validations']+=1
 return validate_road_record(context,source,bounds)
def install():
 global installed
 if installed:return
 s=textwrap.dedent(inspect.getsource(original));needle='if source.descriptor in visited and not source.missing:self._record(source)'
 assert s.count(needle)==1
 s=s.replace(needle,'if source.descriptor in visited and not source.missing:validate(self.older.graph.context,source,(0,239,0,159))')
 ns=dict(original.__globals__,validate=validate);exec(compile(s,'validated-lazy-road-records','exec'),ns);SampledRoadSequence.__init__=ns['__init__'];installed=True
def uninstall():
 global installed
 if not installed:return
 SampledRoadSequence.__init__=original;installed=False

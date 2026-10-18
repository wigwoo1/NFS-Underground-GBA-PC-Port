import inspect,textwrap
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
from owned_serialized_preparation_rows_candidate import PreparationRows
source=inspect.getsource(Adapter.__init__)
needle='self.stage_samples=[]';assert source.count(needle)==1
source=source.replace(needle,'self.stage_samples=PreparationRows()')
namespace=dict(Adapter.__init__.__globals__,PreparationRows=PreparationRows)
exec(compile(textwrap.dedent(source),'serialized-preparation-diagnostic-rows','exec'),namespace)
Adapter.__init__=namespace['__init__']

original_close=Adapter.close
def close(self):
 original_close(self)
 assert isinstance(self.stage_samples,PreparationRows)
 assert all(type(row)is bytes for row in self.stage_samples.rows)
 self.serialized_diagnostic_evidence=dict(rows=len(self.stage_samples),serialized_bytes=sum(len(row) for row in self.stage_samples.rows),selected=True)
 print('SERIALIZED_PREPARATION_RETAINED',self.serialized_diagnostic_evidence,flush=True)
Adapter.close=close

"""Isolated 2048-row bounded diagnostic window for two-minute coverage."""
import inspect,textwrap,pickle
import owned_serialized_preparation_rows_install_candidate as serialized
from owned_serialized_preparation_rows_candidate import PreparationRows
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
class LongPreparationRows(PreparationRows):
 def append(self,row):
  if len(self.rows)>=2048:raise ValueError('Preparation diagnostic capacity exceeded')
  self.rows.append(pickle.dumps(row,protocol=5))
namespace=dict(Adapter.__init__.__globals__,PreparationRows=LongPreparationRows)
exec(compile(textwrap.dedent(serialized.source),'long-preparation-diagnostic-init','exec'),namespace)
Adapter.__init__=namespace['__init__']
source=textwrap.dedent(inspect.getsource(Adapter._run));needle='len(self.stage_samples)<1000';assert source.count(needle)==1
source=source.replace(needle,'len(self.stage_samples)<2048')
namespace=dict(Adapter._run.__globals__);exec(compile(source,'long-preparation-diagnostic-run','exec'),namespace);Adapter._run=namespace['_run']
print('LONG_PREPARATION_ROWS_2048_SELECTED',flush=True)

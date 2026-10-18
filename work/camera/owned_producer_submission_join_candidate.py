"""Join producer and submission records before bounded retention drops them."""
import json
from owned_serialized_recent_rows_candidate import RecentRows
from owned_producer_long_scene_candidate import ProducerRows as Base
latest=None
class SubmissionRows(RecentRows):
 def append(self,row):
  global latest
  super().append(row);latest=json.dumps(row,separators=(',',':'),allow_nan=False)
class ProducerRows(Base):
 def append(self,row):
  joined=dict(row);assert latest is not None
  worker=json.loads(latest)
  assert worker['scene_identity'][1]==row['refresh'] and not worker['replay']
  assert row['started_ns']<=worker['submit_begin_ns']<=worker['submit_end_ns']<=row['completed_ns']
  joined['worker_submission']=worker
  super().append(joined)

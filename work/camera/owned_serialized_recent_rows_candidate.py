"""Bounded immutable serialized diagnostics, decoded only when requested."""
from owned_recent_rows_candidate import RecentRows as Base
import json
class RecentRows(Base):
 def append(self,row):
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False)
  if len(encoded.encode())>self.max_record_bytes:raise ValueError('Diagnostic row exceeds configured byte limit')
  self.rows.append(encoded);self.total_records+=1
 def snapshot(self):return [json.loads(row) for row in self.rows]

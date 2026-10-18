from owned_preparation_pipeline import PreparationPipeline
class Result:
 def close(self):pass
for render_capacity in (3,6,8):
 # Retained chain has render capacity+3 scenes, hence capacity+2 intervals.
 pipeline=PreparationPipeline(render_capacity+2)
 try:
  futures=[pipeline.submit(Result,timeout=.5) for _ in range(render_capacity+2)]
  for future in futures:future.result(2)
  assert len(pipeline.ready)==render_capacity+2
  for future in futures:pipeline.take(future).close()
  assert not pipeline.ready
 finally:pipeline.close()
for capacity in (0,11):
 try:PreparationPipeline(capacity)
 except ValueError:pass
 else:raise AssertionError('Unbounded pipeline accepted')
print('PASS paused maximal retained chain fits bounded preparation capacity and all results retire')

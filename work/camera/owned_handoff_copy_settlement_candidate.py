"""Exactly-once reservation settlement for background native publications.
notify must enqueue atomically or raise before enqueueing. retire invalidates native
publication before a failed notification's reservation is returned.
"""
import threading
from concurrent.futures import CancelledError
class CopySettlement:
 def __init__(self,notify,release,retire,fail):
  self.notify=notify;self.release=release;self.retire=retire;self.fail=fail
  self.lock=threading.Lock();self.settled=False;self.outcome=None;self.errors=[];self.reservation_returned=False
 def __call__(self,future):
  with self.lock:
   if self.settled:return
   self.settled=True
  try:
   result=future.result()
   if type(result) is not dict or type(result.get('published')) is not bool or type(result.get('epoch')) is not int or type(result.get('generation')) is not int or result['epoch']<=0 or result['generation']<=0:raise ValueError('Invalid publication receipt')
   if result['published']:
    self.notify(result);self.outcome='notified';return
   self.outcome='retired';self._release_once();return
  except CancelledError:
   self.outcome='cancelled';self._release_once();return
  except BaseException as exc:
   self.outcome='failed';self.errors.append(repr(exc))
   try:self.retire()
   except BaseException as retirement:self.errors.append(repr(retirement));self.outcome='failed_retirement'
   else:
    try:self._release_once()
    except BaseException as reservation:self.errors.append(repr(reservation))
   try:self.fail(tuple(self.errors))
   except BaseException as reporting:self.errors.append(repr(reporting))
 def _release_once(self):
  with self.lock:
   if self.reservation_returned:return
   self.reservation_returned=True
  self.release()


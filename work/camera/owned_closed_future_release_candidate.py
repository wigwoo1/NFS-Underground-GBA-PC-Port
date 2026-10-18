"""Opt-in successful closed-pair backreference release; external Futures unchanged."""
import weakref
from concurrent.futures import Future
from owned_progressive_pair_candidate import ProgressivePair
from owned_progressive_preparation_adapter_candidate import HistoryOnlyPair

def install(cls):
 original_close=cls.close
 def read_first(self):
  strong=self.__dict__.get('_first_owner')
  if strong is not None:return strong
  ref=self.__dict__.get('_first_weak');value=None if ref is None else ref()
  if value is None:
   # No caller retains the previous successful closed Future. Preserve result semantics.
   if not self.closed:raise RuntimeError('Missing live first-ready owner')
   value=Future();value.set_result(self);self.__dict__['_first_weak']=weakref.ref(value)
  return value
 def get_first(self):
  with self.cv:return read_first(self)
 def set_first(self,value):
  self.__dict__['_first_owner']=value;self.__dict__['_first_weak']=weakref.ref(value)
 def close(self):
  original_close(self)
  with self.cv:
   value=get_first(self)
   if value.done() and not value.cancelled() and value.exception() is None and value.result() is self:
    self.__dict__['_first_weak']=weakref.ref(value);self.__dict__['_first_owner']=None
 cls.first=property(get_first,set_first);cls.close=close
install(ProgressivePair);install(HistoryOnlyPair)

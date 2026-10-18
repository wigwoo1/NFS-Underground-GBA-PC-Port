"""Isolated eight-owner record cache; parsing and private caller copies unchanged."""
from pathlib import Path
import sys
import owned_motion_pairs as original
source=Path(original.__file__).read_text();begin=source.index('def records(');end=source.index('\ndef plan_pair',begin)
namespace=dict(vars(original));exec(compile(source[begin:end].replace('entries[-4:]','entries[-8:]'),'record_cache_eight', 'exec'),namespace)
candidate=namespace['records']
def install():
 previous=original.records
 for name,module in list(sys.modules.items()):
  if module is not None and (name.startswith('owned_') or name.startswith('sample')) and vars(module).get('records') is previous:module.records=candidate
 original.records=candidate

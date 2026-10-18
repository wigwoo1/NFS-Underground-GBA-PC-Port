"""Reuse immutable fully attached endpoint only after original validation succeeds."""
from pathlib import Path
import owned_sky_frame as original
source=Path(original.__file__).read_text()
needle="   if view[offset+10560:offset+25696]!=indices:raise ValueError('Conflicting original sky ownership')"
assert source.count(needle)==1
source=source.replace(needle,needle+'\n   if type(frame) is bytes:return frame')
ns=dict(__name__=__name__);exec(compile(source,str(Path(__file__)),'exec'),ns)
attach_sky=ns['attach_sky']
def install():original.attach_sky=attach_sky

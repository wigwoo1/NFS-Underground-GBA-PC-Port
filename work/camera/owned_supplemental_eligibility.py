"""Resolve supplemental eligibility only for callbacks with a proven flag invariant."""
import struct
from owned_object_filter import eligibility

def supplemental_eligibility(source):
 decision=eligibility(source)
 if decision!='callback':return decision
 selector=struct.unpack_from('<H',source,78)[0]
 if selector!=12:raise ValueError('Unverified supplemental callback selector')
 # Recovered selector12 writes height/mode/damage/angle/projection slot and
 # flags at offset10. It never writes eligibility flags at offset8.
 # This resolves selection only; it does not replay callback side effects.
 return 'project' if struct.unpack_from('<H',source,8)[0]&4 else 'hidden'

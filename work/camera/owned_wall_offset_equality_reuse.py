"""Reuse exact equality only for the same immutable endpoint owners."""
def offsets_equal(portal,metadata):
 old,new=portal.older,portal.newer
 cached=getattr(portal,'_offset_equality_owners',None)
 if cached is not None and cached[0] is old and cached[1] is new:return cached[2]
 equal=metadata(portal,old)[2]==metadata(portal,new)[2]
 portal._offset_equality_owners=(old,new,equal)
 return equal

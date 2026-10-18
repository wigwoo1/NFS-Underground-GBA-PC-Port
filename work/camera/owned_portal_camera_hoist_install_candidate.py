"""Explicit binding of the existing rejected hoist; no automatic installation."""
import types
import owned_portal_traversal as traversal
import owned_motion_visibility as visibility
from owned_portal_helper_hoist_candidate import traverse as hoisted
original=traversal.traverse
candidate=types.FunctionType(hoisted.__code__,traversal.__dict__,'traverse',original.__defaults__)
def install():visibility.traverse=candidate
def restore():visibility.traverse=original

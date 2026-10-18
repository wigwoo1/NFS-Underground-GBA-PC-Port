"""Retain two fixed ABI type definitions; every native call gets fresh storage."""
import ctypes as C,inspect,textwrap
import owned_closed_viewport as viewport
import owned_endpoint_road_planner as planner
Viewport16=C.c_char*16
RoadBounds4=C.c_uint16*4
method=viewport.ClosedViewport.capture.__func__;source=textwrap.dedent(inspect.getsource(method));assert source.count('C.create_string_buffer(16)')==1;source=source.replace('C.create_string_buffer(16)','Viewport16()')
ns=dict(method.__globals__);ns.update(Viewport16=Viewport16);exec(compile(source,'fixed-viewport-type','exec'),ns);viewport.ClosedViewport.capture=ns['capture']
method=planner.EndpointRoadPlanner.plan;source=textwrap.dedent(inspect.getsource(method));old="(C.c_uint16*4)(*item['bounds'])";new="RoadBounds4(*item['bounds'])";assert source.count(old)==1;source=source.replace(old,new)
ns=dict(method.__globals__);ns.update(RoadBounds4=RoadBounds4);exec(compile(source,'fixed-road-bounds-type','exec'),ns);planner.EndpointRoadPlanner.plan=ns['plan']

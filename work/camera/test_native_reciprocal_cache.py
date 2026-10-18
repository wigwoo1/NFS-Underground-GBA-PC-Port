import threading
from owned_endpoint_road_selection import _native_reciprocal
values=tuple(range(32768));a=_native_reciprocal(values);assert _native_reciprocal(values) is a and tuple(a)==values
other=tuple(list(values));assert _native_reciprocal(other) is not a
mutable=list(values);first=_native_reciprocal(mutable);mutable[0]=123;second=_native_reciprocal(mutable);assert first[0]==0 and second[0]==123
out=[];t=threading.Thread(target=lambda:out.append(_native_reciprocal(values)));t.start();t.join();assert out[0] is not a and tuple(out[0])==values
print('PASS native reciprocal exact bytes, identity/thread isolation and mutable input freshness')

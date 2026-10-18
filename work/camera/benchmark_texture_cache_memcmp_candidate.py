import ctypes as C,statistics,time
import owned_source_d3d_texture_backdrop_consumer_memcmp_candidate as candidate
n=240*160*4
data=bytes(range(256))*(n//256)
source=C.create_string_buffer(data);pointer=C.cast(source,C.c_void_p)
cached=(240,160,data);cache={7:cached}
mem=candidate.MEMCMP
def old():
 for _ in range(1000):
  current=(240,160,C.string_at(pointer,n))
  assert cache.get(7)==current
def new():
 for _ in range(1000):
  old=cache.get(7)
  assert old[0]==240 and old[1]==160 and len(old[2])==n and mem(pointer,old[2],n)==0
old();new()
a=[];b=[]
for _ in range(5):
 t=time.perf_counter_ns();old();a.append((time.perf_counter_ns()-t)/1e6)
 t=time.perf_counter_ns();new();b.append((time.perf_counter_ns()-t)/1e6)
print({'bytes_per_check':n,'checks_per_round':1000,'old_copy_compare_ms':a,'new_in_place_compare_ms':b,'old_median_ms':statistics.median(a),'new_median_ms':statistics.median(b),'relative_ratio':statistics.median(b)/statistics.median(a)})
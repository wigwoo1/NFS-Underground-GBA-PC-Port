import ctypes as C,time
from pathlib import Path
helper=C.CDLL(str(Path(__file__).with_name('backdrop-call-profile.dll')))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint64
helper.nf_profile_pointer_call.argtypes=[P,P,C.POINTER(U),S];helper.nf_profile_pointer_call.restype=C.c_int
helper.nf_profile_buffer_call.argtypes=[P,P,S,C.POINTER(U),S];helper.nf_profile_buffer_call.restype=C.c_int
def call(self,name,fn,data,size=None):
    if not hasattr(self,'backdrop_profile_buffer'):self.backdrop_profile_buffer=(U*4)()
    begin=time.perf_counter_ns();address=C.cast(fn,P)
    if size is None:result=helper.nf_profile_pointer_call(address,data,self.backdrop_profile_buffer,32)
    else:result=helper.nf_profile_buffer_call(address,data,size,self.backdrop_profile_buffer,32)
    end=time.perf_counter_ns();a,b,c,d=self.backdrop_profile_buffer
    self.backdrop_call_profiles.append(dict(call=name,caller_begin_ns=begin,caller_end_ns=end,native_begin_ns=a,native_end_ns=b,native_cycles=d-c))
    return result
def transform(source,namespace):
    marker='ticks=[time.perf_counter_ns()];self.stage_profile=[]'
    assert source.count(marker)==1
    source=source.replace(marker,marker+';self.backdrop_call_profiles=[]')
    for original,replacement in (
        ('d.nf_d3d_clear(F32_4(.035,.05,.08,1))','backdrop_call(self,"clear",d.nf_d3d_clear,F32_4(.035,.05,.08,1))'),
        ('s.nf_source_backdrop_copy(rows,640)','backdrop_call(self,"backdrop_copy",s.nf_source_backdrop_copy,rows,640)'),
        ('d.nf_d3d_backdrop_rows(rows,640)','backdrop_call(self,"backdrop_draw",d.nf_d3d_backdrop_rows,rows,640)')):
        assert source.count(original)==1;source=source.replace(original,replacement)
    marker="stage('backdrop_geometry')"
    assert source.count(marker)==1
    source=source.replace(marker,marker+";self.stage_profile[-1]['native_calls']=self.backdrop_call_profiles")
    namespace['backdrop_call']=call
    return source

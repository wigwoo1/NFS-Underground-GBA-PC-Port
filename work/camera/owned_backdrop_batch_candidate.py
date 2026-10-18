import ctypes as C
from pathlib import Path
helper=C.CDLL(str(Path(__file__).with_name('backdrop-batch.dll')))
P=C.c_void_p;S=C.c_size_t
helper.nf_backdrop_batch.argtypes=[P]*6+[S];helper.nf_backdrop_batch.restype=C.c_int
def draw(self,s):
    if not hasattr(self,'backdrop_batch_args'):
        self.backdrop_batch_color=(C.c_float*4)(.035,.05,.08,1)
        self.backdrop_batch_args=(C.cast(self.d.nf_d3d_clear,P),C.cast(s.nf_source_backdrop_count,P),
            C.cast(s.nf_source_backdrop_copy,P),C.cast(self.d.nf_d3d_backdrop_rows,P),
            self.backdrop_batch_color,self.backdrop_scratch,640)
        self.backdrop_batch_source=s
        self.backdrop_batch_calls=0
    if s is not self.backdrop_batch_source:raise RuntimeError('Backdrop batch source owner changed')
    result=helper.nf_backdrop_batch(*self.backdrop_batch_args)
    assert result==0,result
    self.backdrop_batch_calls+=1
def transform(source,namespace):
    assert source.count('quad(')==1 # Existing local helper has no call sites.
    start=source.index('  assert d.nf_d3d_clear(')
    end=source.index("  stage('backdrop_geometry')",start)
    source=source[:start]+'  backdrop_batch(self,s)\n'+source[end:]
    marker="stage('backdrop_geometry')"
    source=source.replace(marker,marker+";self.stage_profile[-1]['backdrop_batch_calls']=self.backdrop_batch_calls")
    namespace['backdrop_batch']=draw
    return source

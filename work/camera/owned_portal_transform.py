"""Original ARM portal horizontal transform, wrapped32-bit Q14 arithmetic."""
def signed32(v):
 v&=0xffffffff
 return v if v<0x80000000 else v-0x100000000
def transform(x,z,m):
 x=signed32(x+m[9]);z=signed32(z+m[11])
 return signed32(x*m[0]+z*m[6])>>14,signed32(x*m[2]+z*m[8])>>14

def trunc_div(a,b):
 if not b:raise ValueError('Zero portal depth span')
 q=abs(a)//abs(b)
 return -q if (a<0)!=(b<0) else q
def project_edge(a,b,near,scale,center,reciprocal,flip=False):
 x,z=a;nx,nz=b
 # Far depth also terminates the original parent traversal; caller must preserve that control flow.
 if z>0x6000 or nz>0x6000 or (z<near and nz<near):return None
 flags=0
 if z<near:
  x=signed32(x+signed32((signed32((near-z)*(nx-x))*signed32(reciprocal[nz-z]))>>24));z=near;flags|=8
 elif nz<near:
  nx=signed32(nx-signed32((signed32((near-nz)*(nx-x))*signed32(reciprocal[z-nz]))>>24));nz=near;flags|=16
 def project(v,d):return center+(signed32((signed32(reciprocal[d]*scale)>>7)*(v>>1))>>16)
 left,right=project(x,z),project(nx,nz)
 if flip and left>right:left,right=right,left
 return left,right,flags,z,nz

"""Source-owned original camera-offset query with rigid endpoint corrections."""
import math

def signed32(value):
 value=int(value)&0xffffffff
 return value-0x100000000 if value&0x80000000 else value

def fixed_offset(matrix):
 # Original query uses transposed camera rotation and zero translation.
 return tuple(signed32(matrix[i*3]*8+matrix[i*3+2]*80)>>14 for i in range(3))

def fixed_queries(matrix):
 offset=fixed_offset(matrix)
 return tuple(tuple(float(signed32(-matrix[9+i]+sign*offset[i])) for i in range(3)) for sign in (1,-1))

def continuous_queries(raw_a,raw_b,endpoints,camera,alpha):
 if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid root query alpha')
 if len(raw_a)!=12 or len(raw_b)!=12 or len(camera)!=12 or len(endpoints)!=2 or any(len(x)!=12 for x in endpoints):raise ValueError('Invalid root query matrices')
 if not all(math.isfinite(v) for m in (camera,*endpoints) for v in m):raise ValueError('Invalid root query camera')
 fixed_a=fixed_queries(raw_a);fixed_b=fixed_queries(raw_b)
 if alpha==0:return fixed_a
 if alpha==1:return fixed_b
 def ideal(matrix,sign):return tuple(-matrix[9+i]+sign*(8*matrix[i*3]+80*matrix[i*3+2]) for i in range(3))
 out=[]
 for index,sign in enumerate((1,-1)):
  a=ideal(endpoints[0],sign);b=ideal(endpoints[1],sign);now=ideal(camera,sign)
  out.append(tuple(now[i]+(1-alpha)*(fixed_a[index][i]-a[i])+alpha*(fixed_b[index][i]-b[i]) for i in range(3)))
 return tuple(out)

"""Raw camera-space endpoint residuals; no screen projection correspondence."""
import struct
def pose_matrix(pose):
 x,y,z,w=pose.rotation.x,pose.rotation.y,pose.rotation.z,pose.rotation.w
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return tuple(rows[r][c] for c in range(3) for r in range(3))+(-pose.position.x,-pose.position.y,-pose.position.z)
def correction(pair,alpha):
 plan,d,ca,cb,*_=pair.arguments
 return (struct.unpack('<12i',plan['camera_older']),struct.unpack('<12i',plan['camera_newer']),pose_matrix(ca),pose_matrix(cb),alpha)

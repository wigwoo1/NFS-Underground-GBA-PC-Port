#include <stdint.h>
#include <string.h>
typedef int (*Read)(void*,uint32_t,void*,size_t);
typedef struct {uint32_t version,address;int32_t matrix[12];} NFRoadCameraMetadata;
/* Obtain raw source camera through the producer's owned reader, atomically.
   Never reconstruct Q14 scale from a normalized quaternion. */
__declspec(dllexport) int nf_road_camera_metadata_owned(const uint8_t state[256],Read read,void*user,NFRoadCameraMetadata*out){
 if(!state||!read||!out)return 0;
 NFRoadCameraMetadata result;result.version=1;memcpy(&result.address,state+84,4);
 if((result.address&3)||(uint64_t)result.address+48>0x100000000ull||!read(user,result.address,result.matrix,48))return 0;
 memcpy(out,&result,sizeof(result));return 1;
}

#include "road_metadata_preview.h"
__declspec(dllexport) int nf_preview_metadata_component(const NFWorldMetadata*m,NFRoadSourceAttributes*a,NFRoadCameraMetadata*c,unsigned*p,unsigned*f){return nf_preview_road_metadata(m,a,c,p,f);}

#include <stdint.h>
#include <stddef.h>
#include <string.h>
/* Original 030002C0: only complete 32-byte groups are written. */
__declspec(dllexport) int nfs_initial_fill(uint8_t*page,size_t size,uint32_t offset,uint32_t value,uint32_t bytes){
 size_t n=(bytes>>5)*32u;
 if(!page||offset>size||n>size-offset)return 0;
 for(size_t i=0;i<n;i++)page[offset+i]=(uint8_t)(value>>((i&3)*8));
 return 1;
}
/* Original 03003814: floor(width/32)+1 groups, all requested rows.
 Source and destination strides are arithmetic-rounded to 2/4 bytes. */
__declspec(dllexport) int nfs_initial_copy(uint8_t*page,size_t size,uint32_t offset,const uint8_t*source,size_t source_size,uint32_t width,uint32_t rows,uint32_t source_stride,uint32_t destination_stride){
 if(!page||!source||width>4096||rows>512||source_stride>4096||destination_stride>4096)return 0;
 if(rows==0)return 1;
 size_t n=((width>>5)+1u)*32u,ss=source_stride&~1u,ds=destination_stride&~3u;
 size_t se=(rows-1)*ss+n,de=(rows-1)*ds+n;
 if(offset>size||de>size-offset||se>source_size)return 0;
 for(size_t r=0;r<rows;r++)memcpy(page+offset+r*ds,source+r*ss,n);
 return 1;
}

/* Original 03000298 contiguous complete 32-byte blocks. */
__declspec(dllexport) int nfs_initial_block_copy(uint8_t*page,size_t size,uint32_t offset,const uint8_t*source,size_t source_size,uint32_t bytes){
 size_t n=(bytes>>5)*32u;
 if(!page||!source||offset>size||n>size-offset||n>source_size)return 0;
 memcpy(page+offset,source,n);return 1;
}

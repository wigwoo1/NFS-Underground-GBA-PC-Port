#include <mgba/core/core.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char**argv){if(argc!=5)return 1;unsigned state=(unsigned)strtoul(argv[3],NULL,0);FILE*f=fopen(argv[2],"rb");unsigned char*ram=malloc(0x48000);if(!f||!ram||fread(ram,1,0x48000,f)!=0x48000)return 2;fclose(f);struct mCore*c=mCoreFind(argv[1]);if(!c||!c->init(c))return 3;mCoreInitConfig(c,"nfsug-isolated-builder");c->opts.useBios=false;c->opts.skipBios=true;uint32_t*pixels=calloc(38400,4);c->setVideoBuffer(c,pixels,240);c->setAudioBufferSize(c,4096);if(!mCoreLoadFile(c,argv[1]))return 4;c->reset(c);struct GBA*g=c->board;memcpy(g->memory.wram,ram,0x40000);memcpy(g->memory.iwram,ram+0x40000,0x8000);struct ARMCore*cpu=c->cpu;cpu->gprs[0]=state;cpu->gprs[13]=0x03007f00;cpu->gprs[14]=0x08000000;_ARMSetMode(cpu,MODE_ARM);cpu->gprs[15]=0x03004c74;ARMWritePC(cpu);unsigned steps=0;for(;steps<2000000;steps++){unsigned pc=cpu->gprs[15]-(cpu->executionMode==MODE_ARM?4:2);if(pc==0x03004d50)break;ARMRun(cpu);}printf("steps=%u pc=%08x\n",steps,cpu->gprs[15]);if(steps==2000000)return 5;memcpy(ram,g->memory.wram,0x40000);memcpy(ram+0x40000,g->memory.iwram,0x8000);f=fopen(argv[4],"wb");if(!f||fwrite(ram,1,0x48000,f)!=0x48000)return 6;fclose(f);mCoreConfigDeinit(&c->config);c->deinit(c);free(ram);free(pixels);return 0;}

from pathlib import Path
p=Path('work/v2/gpu.c');s=p.read_text();s+='''
unsigned nf_gpu_frame_hash(void){
 static unsigned pixels[1000*600];unsigned hash=2166136261u;
 BindFramebuffer(FB,fbo);glReadPixels(1200,600,1000,600,GL_RGBA,GL_UNSIGNED_BYTE,pixels);BindFramebuffer(FB,0);
 for(unsigned i=0;i<1000*600;i++)hash=(hash^pixels[i])*16777619u;
 return hash;
}
''';p.write_text(s)
p=Path('work/v2/gpu.h');s=p.read_text().replace('#endif','unsigned nf_gpu_frame_hash(void);\n#endif');p.write_text(s)
p=Path('work/host.c');s=p.read_text().replace('static FILE* diagnostic;','static FILE* diagnostic;\nstatic FILE* frame_audit;');s=s.replace('else if(!strcmp(argv[i],"--test-realtime"))','else if(!strcmp(argv[i],"--audit-frames")&&i+1<argc){frame_audit=fopen(argv[++i],"w");if(frame_audit)fprintf(frame_audit,"seconds,emuframe,hash,mode60,polygons\\n");}else if(!strcmp(argv[i],"--test-realtime"))');s=s.replace('if(!draw())errors++;displayframes++;','if(!draw())errors++;displayframes++;\n  if(frame_audit)fprintf(frame_audit,"%.6f,%d,%08x,%d,%d\\n",now(),emuframes,nf_gpu_frame_hash(),mode60,nf_gpu_polygon_count());');s=s.replace('if(xi)FreeLibrary(xi);','if(frame_audit)fclose(frame_audit);\n if(xi)FreeLibrary(xi);');p.write_text(s)

package org.codex.nfsugpreview;
import java.nio.*;
/** Validated owned packet world/order metadata. No raster/visibility synthesis. */
final class NativeWorldScene {
 static final class Surface {
  final int corners,width,height,kind,mode,planes;final boolean lit;
  private final ByteBuffer source,metadata,lighting;private final long[] identity;
  Surface(ByteBuffer source,ByteBuffer metadata,ByteBuffer lighting,long[] identity,int mode,boolean lit){this.source=source;this.metadata=metadata;this.lighting=lighting;this.identity=identity;this.mode=mode;this.lit=lit;corners=source.getInt(0);width=source.getInt(4);height=source.getInt(8);kind=(int)identity[0];planes=mode==3||mode==8?17:1;}
  ByteBuffer vertices(){return slice(source,12,corners*24);}ByteBuffer uv(){return slice(source,12+corners*24,corners*16);}ByteBuffer texture(){return slice(source,12+corners*40,width*height*4);}
  ByteBuffer metadata(){return metadata.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}ByteBuffer lighting(){return lighting.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}long[] identity(){return identity.clone();}
  ByteBuffer states(){return mode==2||mode==3||mode==7||mode==8?slice(metadata,0,width*height*planes):null;}
  ByteBuffer originalIndices(){int pixels=width*height;if(mode==7||mode==8)return slice(metadata,pixels*planes,pixels*planes);return mode==1||mode==4||mode==5||mode==6||mode==9||mode==10?slice(metadata,0,pixels):null;}
  ByteBuffer sourceAttributes(){return mode==5||mode==6||mode==9||mode==10?slice(metadata,metadata.remaining()-288,288):null;}
  ByteBuffer sourceCamera(){return mode==9||mode==10?slice(metadata,width*height,56):null;}
 }
 static final class Command {final boolean model;final int index;Command(boolean model,int index){this.model=model;this.index=index;}}
 private final Surface[] surfaces;private final Command[] commands;private final ByteBuffer reciprocal,bounds;final int modelCount;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Invalid native world/order");}
 private static long word(ByteBuffer b,int at){return Integer.toUnsignedLong(b.getInt(at));}
 private static ByteBuffer slice(ByteBuffer source,int offset,int size){need(offset>=0&&size>=0&&offset<=source.remaining()&&size<=source.remaining()-offset);ByteBuffer b=source.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);b.position(offset);b.limit(offset+size);return b.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 private static double number(ByteBuffer b,int at){double v=b.getDouble(at);need(Double.isFinite(v));return v;}
 NativeWorldScene(NativeScenePacket packet){
  modelCount=NativeModelMesh.modelCount(packet);ByteBuffer world=packet.section(1);need(world.remaining()>=8&&word(world,0)==0x31444652L&&word(world,4)<=128);int n=(int)word(world,4),at=8;
  ByteBuffer[] raw=new ByteBuffer[n],metadata=new ByteBuffer[n],lights=new ByteBuffer[n];int[] modes=new int[n];boolean[] lit=new boolean[n];long[][] identities=new long[n][];
  for(int i=0;i<n;i++){need(world.remaining()-at>=12);long count=word(world,at),width=word(world,at+4),height=word(world,at+8);need(count>=3&&count<=32&&width>0&&width<=1024&&height>0&&height<=1024);long bytes=12+count*40+width*height*4;need(bytes<=world.remaining()-at);raw[i]=slice(world,at,(int)bytes);for(int j=0;j<count*5;j++)number(raw[i],12+j*8);at+=bytes;metadata[i]=slice(world,at,0);}
  if(at!=world.remaining()){
   need(world.remaining()-at>=8&&word(world,at)==0x3149574eL&&word(world,at+4)==n);at+=8;
   for(int i=0;i<n;i++){need(world.remaining()-at>=8);long mode=word(world,at),bytes=word(world,at+4);at+=8;need(mode<=10&&bytes<=world.remaining()-at);int pixels=raw[i].getInt(4)*raw[i].getInt(8);long expected=(long)pixels*(mode==3?17:mode==7?2:mode==8?34:1)+(mode==5||mode==6?288:mode==9||mode==10?344:0);need(mode==0?bytes==0:bytes==expected);modes[i]=(int)mode;metadata[i]=slice(world,at,(int)bytes);validateMetadata(raw[i],metadata[i],(int)mode);at+=bytes;}need(at==world.remaining());
  }
  ByteBuffer id=packet.section(4);int entries=n+modelCount,base=8+entries*20;need(id.remaining()>=base&&word(id,0)==0x3149464eL&&word(id,4)==entries);
  for(int i=0;i<entries;i++){long kind=word(id,8+i*20);need(i>=n?kind==3:kind==1||kind==2);if(i<n){identities[i]=new long[5];for(int j=0;j<5;j++)identities[i][j]=word(id,8+i*20+j*4);int mode=modes[i];need(!((mode==2||mode==3||mode==7||mode==8)&&kind!=2)&&!((mode==1||mode==4||mode==5||mode==6)&&kind!=1));}}
  if(id.remaining()!=base){need(id.remaining()-base>=16);long magic=word(id,base),count=word(id,base+4);need((magic==0x3142464eL&&count==n)||(magic==0x3242464eL&&count==entries));need(id.remaining()==base+16+count*8);double alpha=number(id,base+8);need(alpha>=0&&alpha<1);for(int i=0;i<count;i++){int pos=base+16+i*8,left=id.getShort(pos)&65535,right=id.getShort(pos+2)&65535,top=id.getShort(pos+4)&65535,bottom=id.getShort(pos+6)&65535;need(left<=right&&right<=240&&top<=bottom&&bottom<=160);}bounds=slice(id,base,id.remaining()-base);}else bounds=slice(id,base,0);
  ByteBuffer order=packet.section(2);need(order.remaining()==8+entries*4&&word(order,0)==0x314f464eL&&word(order,4)==entries);commands=new Command[entries];boolean[] seen=new boolean[entries];
  for(int i=0;i<entries;i++){long value=word(order,8+i*4);boolean model=value>=0xfffffff0L;long index=model?0xffffffffL-value:value;need(index<(model?modelCount:n));int slot=(int)index+(model?n:0);need(!seen[slot]);seen[slot]=true;commands[i]=new Command(model,(int)index);}
  ByteBuffer lighting=packet.section(3);need(lighting.remaining()>=8&&word(lighting,0)==0x314c464eL&&word(lighting,4)==n);at=8;
  for(int i=0;i<n;i++){need(lighting.remaining()-at>=4);long enabled=word(lighting,at);int start=at;at+=4;int mode=modes[i];need(enabled<=1&&!((mode==2||mode==4||mode==5||mode==6||mode==7||mode==9||mode==10)&&enabled!=0)&&!((mode==3||mode==8)&&enabled==0));lit[i]=enabled!=0;if(lit[i]){need(lighting.remaining()-at>=16&&word(lighting,at)<=15&&word(lighting,at+4)<=15&&word(lighting,at+8)==raw[i].getInt(4)&&word(lighting,at+12)==raw[i].getInt(8));long bytes=16L+raw[i].getInt(4)*raw[i].getInt(8)*64L;need(bytes<=lighting.remaining()-at);at+=bytes;}lights[i]=slice(lighting,start,at-start);}
  need(lighting.remaining()-at==32768*4);reciprocal=slice(lighting,at,32768*4);surfaces=new Surface[n];for(int i=0;i<n;i++)surfaces[i]=new Surface(raw[i],metadata[i],lights[i],identities[i],modes[i],lit[i]);
 }
 private static void validateMetadata(ByteBuffer surface,ByteBuffer data,int mode){
  int count=surface.getInt(0),width=surface.getInt(4),height=surface.getInt(8),pixels=width*height;
  if(mode==5||mode==6||mode==9||mode==10){int extra=mode>=9?56:0,at=pixels+extra;if(extra!=0)need(word(data,pixels)==1&&word(data,pixels+4)%4==0&&word(data,pixels+4)+48<=0x100000000L);
   need(word(data,at)==count&&word(data,at+4)<=10&&(1L<<word(data,at+4))==width&&word(data,at+8)==height*2&&word(data,at+12)==(mode==6||mode==10?1:0)&&word(data,at+16)!=0&&word(data,at+16)%4==0&&word(data,at+20)!=0&&word(data,at+20)%2==0);int u=data.getInt(at+24),v=data.getInt(at+28);need(u>=-32768&&u<=32767&&v>=-32768&&v<=32767);
   for(int i=0;i<32;i++){int x=data.getInt(at+32+i*8),y=data.getInt(at+36+i*8);if(i>=count)need(x==0&&y==0);else{double expectedU=x/16384.0+u/(256.0*width),expectedV=y/16384.0+v/(512.0*height);need(Math.abs(surface.getDouble(12+count*24+i*16)-expectedU)<=1e-10&&Math.abs(surface.getDouble(20+count*24+i*16)-expectedV)<=1e-10);}}
  }
  if(mode==2||mode==3||mode==7||mode==8){int planes=mode==3||mode==8?17:1,bytes=pixels*planes;for(int i=0;i<bytes;i++){int state=data.get(i)&255;need(state<=2);if(mode==7||mode==8)need((state==2)==((data.get(bytes+i)&255)!=0));}for(int i=0;i<pixels;i++){int state=data.get(i)&255;need(state!=1);for(int level=1;level<planes;level++)need((state==0)==(data.get(level*pixels+i)==0));}}
 }
 int surfaceCount(){return surfaces.length;}int commandCount(){return commands.length;}
 Surface surface(int index){if(index<0||index>=surfaces.length)throw new IllegalArgumentException("Surface index");return surfaces[index];}
 Command command(int index){if(index<0||index>=commands.length)throw new IllegalArgumentException("Command index");return commands[index];}
 ByteBuffer reciprocal(){return reciprocal.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}ByteBuffer bounds(){return bounds.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
}

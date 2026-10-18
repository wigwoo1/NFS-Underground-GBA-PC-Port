package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Original road-event history only. Non-road overwrite ownership is separate. */
final class NativeRoadHistory {
 static final class Event{final long ordinal,refresh,address;private final ByteBuffer commands,texture;final int count,assetKey;
  Event(long ordinal,long refresh,long address,int count,int assetKey,ByteBuffer commands,ByteBuffer texture){this.ordinal=ordinal;this.refresh=refresh;this.address=address;this.count=count;this.assetKey=assetKey;this.commands=commands;this.texture=texture;}
  ByteBuffer texture(){return texture.asReadOnlyBuffer();}
 }
 static final class Samples{private final int[] events,offsets;Samples(int[] e,int[] o){events=e;offsets=o;}int event(int cell){return events[cell];}int offset(int cell){return offsets[cell];}}
 private final Event[] events;final long epoch;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Invalid road history");}
 private static ByteBuffer slice(ByteBuffer b,int at,int count){ByteBuffer v=b.duplicate().order(ByteOrder.LITTLE_ENDIAN);v.position(at);v.limit(at+count);return v.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 NativeRoadHistory(byte[] input){
  if(input!=null&&input.length>=4&&ByteBuffer.wrap(input).order(ByteOrder.LITTLE_ENDIAN).getInt(0)==0x3148524e){Compact compact=compact(input);epoch=compact.epoch;events=compact.events;return;}
  need(input!=null&&input.length>=96&&input.length<=64*1024*1024);ByteBuffer b=ByteBuffer.wrap(input.clone()).order(ByteOrder.LITTLE_ENDIAN);ArrayList<Event> list=new ArrayList<Event>();int at=0;long previous=0,previousRefresh=0,ownedEpoch=0;
  while(at<input.length){need(input.length-at>=96);long[] h=new long[12];for(int i=0;i<12;i++)h[i]=b.getLong(at+i*8);need(h[0]==0x314a524eL&&h[1]==1&&h[3]>0&&h[4]>previous&&h[5]>=previousRefresh&&h[5]<=0xffffffffL&&h[6]==1&&h[7]>=0&&h[7]<=8192&&h[8]>=0&&h[8]<=15&&h[9]>=0x08000000L&&h[9]<0x0a000000L&&h[10]>0&&h[10]<=0x1000000&&h[10]<=0x0a000000L-h[9]&&h[11]==17);
   need(h[2]==96+h[7]*68+h[10]&&h[2]<=input.length-at);if(ownedEpoch==0)ownedEpoch=h[3];need(h[3]==ownedEpoch);int count=(int)h[7];ByteBuffer commands=slice(b,at+96,count*68),texture=slice(b,at+96+count*68,(int)h[10]);
   for(int i=0;i<count;i++){int p=i*68,shift=commands.getInt(p),width=commands.getInt(p+28),duplicate=commands.getInt(p+64);long destination=Integer.toUnsignedLong(commands.getInt(p+24));need(shift>=0&&shift<=15&&width>=0&&width<=512&&duplicate>=0&&duplicate<=1&&commands.getInt(p+4)>=0&&commands.getInt(p+8)>=0&&destination>=0x06000000L&&destination<=0x06014000L&&destination+width*2L+duplicate*240<=0x06014000L);}
   list.add(new Event(h[4],h[5],h[9],count,list.size()+1,commands,texture));need(list.size()<=4096);at+=(int)h[2];previous=h[4];previousRefresh=h[5];
  }need(at==input.length);epoch=ownedEpoch;events=list.toArray(new Event[list.size()]);
 }
 private static final class Compact{final long epoch;final Event[] events;Compact(long e,Event[] v){epoch=e;events=v;}}
 private static Compact compact(byte[] input){
  need(input.length>=64&&input.length<=64*1024*1024);ByteBuffer b=ByteBuffer.wrap(input.clone()).order(ByteOrder.LITTLE_ENDIAN);need(b.getLong(0)==0x3148524eL&&b.getLong(8)==1&&b.getLong(16)==input.length&&b.getLong(24)>0&&b.getLong(32)>0&&b.getLong(32)<=1024&&b.getLong(40)>0&&b.getLong(40)<=65536&&b.getLong(48)==0&&b.getLong(56)==0);
  ArrayList<ByteBuffer> assets=new ArrayList<ByteBuffer>();ArrayList<Long> addresses=new ArrayList<Long>();ArrayList<Event> list=new ArrayList<Event>();long previous=0,frame=0,payload=0;int at=64;
  while(at<input.length){need(input.length-at>=64);long tag=b.getLong(at),size=b.getLong(at+8);need(size>=64&&size<=input.length-at);
   if(tag==1){long id=b.getLong(at+16),address=b.getLong(at+32),bytes=b.getLong(at+40);need(assets.size()<b.getLong(32)&&id==assets.size()+1&&b.getLong(at+24)==1&&address>=0x08000000L&&bytes>0&&bytes<=0x1000000&&address<=0x0a000000L-bytes&&size==64+bytes&&b.getLong(at+48)==0&&b.getLong(at+56)==0);payload+=bytes;need(payload<=32*1024*1024);assets.add(slice(b,at+64,(int)bytes));addresses.add(address);}
   else {need(tag==2&&size==164&&list.size()<b.getLong(40));long ordinal=b.getLong(at+16),refresh=b.getLong(at+24),id=b.getLong(at+32),address=b.getLong(at+48),shift=b.getLong(at+64);need(ordinal>previous&&refresh>=frame&&refresh<=0xffffffffL&&id>0&&id<=assets.size()&&b.getLong(at+40)==0&&address==addresses.get((int)id-1)&&b.getLong(at+56)==1&&shift>=0&&shift<=15&&b.getLong(at+72)==0&&b.getLong(at+80)==0&&b.getLong(at+88)==0);
    ByteBuffer command=slice(b,at+96,68);int width=command.getInt(28),duplicate=command.getInt(64);long destination=Integer.toUnsignedLong(command.getInt(24));need(command.getInt(0)>=0&&command.getInt(0)<=15&&command.getInt(4)>=0&&command.getInt(8)>=0&&width>=0&&width<=512&&duplicate>=0&&duplicate<=1&&destination>=0x06000000L&&destination+width*2L+duplicate*240<=0x06014000L);
    list.add(new Event(ordinal,refresh,address,1,(int)id,command,assets.get((int)id-1)));previous=ordinal;frame=refresh;
   }at+=(int)size;
  }need(at==input.length&&assets.size()==b.getLong(32)&&list.size()==b.getLong(40));return new Compact(b.getLong(24),list.toArray(new Event[list.size()]));
 }
 int count(){return events.length;}Event event(int index){return events[index];}
 Samples samples(long expectedEpoch,long end,int page){
  need(expectedEpoch==epoch&&end>=0&&end<=0xffffffffL&&(page==0||page==1));int[] ids=new int[38400],offsets=new int[38400];Arrays.fill(ids,-1);Arrays.fill(offsets,-1);
  for(int index=0;index<events.length;index++){Event event=events[index];if(event.refresh>end)break;ByteBuffer b=event.commands;
   for(int i=0;i<event.count;i++){int at=i*68,shift=b.getInt(at),u=b.getInt(at+32),v=b.getInt(at+36),um=b.getInt(at+4),vm=b.getInt(at+8),width=b.getInt(at+28),du=b.getInt(at+40),dv=b.getInt(at+44),duplicate=b.getInt(at+64);long source=Integer.toUnsignedLong(b.getInt(at+20)),destination=Integer.toUnsignedLong(b.getInt(at+24));
    int[] sourceOffsets=new int[width];for(int k=0;k<width;k++){u&=um;v&=vm;long offset=source+2*((u>>>16)+((long)(v>>>16)<<shift))-event.address;need(offset>=0&&offset+2<=event.texture.remaining());sourceOffsets[k]=(int)offset;u+=du;v+=dv;}
    // Original writer copies the complete first row, then the doubled row.
    for(int d=0;d<=duplicate;d++)for(int k=0;k<width;k++)for(int lane=0;lane<2;lane++){long cell=destination+k*2L+d*240+lane-(0x06000000L+page*0xa000L);if(cell>=0&&cell<38400){ids[(int)cell]=index;offsets[(int)cell]=sourceOffsets[k]+lane;}}
   }
  }return new Samples(ids,offsets);
 }
}

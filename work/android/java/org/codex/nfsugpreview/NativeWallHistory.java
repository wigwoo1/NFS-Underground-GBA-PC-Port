package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Immutable original span commands and assets; no finished pixels. */
final class NativeWallHistory {
 private static final class Asset {final long address;final int category;final ByteBuffer data;Asset(long a,int c,ByteBuffer d){address=a;category=c;data=d;}}
 private static final class Event {final long refresh;final int texture,shade;final int[] command;Event(long r,int t,int s,int[] c){refresh=r;texture=t;shade=s;command=c;}}
 static final class Samples {private final int[] assets,offsets;private final long[] refreshes;Samples(int[] a,int[] o,long[] r){assets=a;offsets=o;refreshes=r;}int asset(int cell){return assets[cell];}int offset(int cell){return offsets[cell];}long refresh(int cell){return refreshes[cell];}}
 final long epoch;private final Asset[] assets;private final Event[] events;
 private static void need(boolean ok){if(!ok)throw new IllegalArgumentException("Invalid original wall history");}
 private static long u(int value){return Integer.toUnsignedLong(value);}
 private static ByteBuffer slice(ByteBuffer b,int at,int count){ByteBuffer v=b.duplicate();v.position(at);v.limit(at+count);return v.slice().asReadOnlyBuffer();}
 NativeWallHistory(byte[] input){
  need(input!=null&&input.length>=64&&input.length<=64*1024*1024);ByteBuffer b=ByteBuffer.wrap(input.clone()).order(ByteOrder.LITTLE_ENDIAN);
  need(b.getLong(0)==0x3148574eL&&b.getLong(8)==1&&b.getLong(16)==input.length&&b.getLong(24)>0&&b.getLong(32)>0&&b.getLong(32)<=1024&&b.getLong(40)>0&&b.getLong(40)<=65536&&b.getLong(48)==0&&b.getLong(56)==0);
  epoch=b.getLong(24);int assetCount=(int)b.getLong(32),eventCount=(int)b.getLong(40),at=64;long previous=0,refresh=0,assetBytes=0;ArrayList<Asset> aa=new ArrayList<Asset>();ArrayList<Event> ee=new ArrayList<Event>();
  while(at<input.length){need(input.length-at>=64);long tag=b.getLong(at),size=b.getLong(at+8);need(size>=64&&size<=input.length-at);
   if(tag==1){long id=b.getLong(at+16),category=b.getLong(at+24),address=b.getLong(at+32),bytes=b.getLong(at+40);need(aa.size()<assetCount&&id==aa.size()+1&&(category==1||category==2)&&bytes==(category==1?65536:4081)&&size==64+bytes&&b.getLong(at+48)==0&&b.getLong(at+56)==0&&address>=0x02000000L&&address<=0x0a000000L-bytes&&(category!=1||address>=0x08000000L));assetBytes+=bytes;need(assetBytes<=32*1024*1024);aa.add(new Asset(address,(int)category,slice(b,at+64,(int)bytes)));}
   else {need(tag==2&&size==176&&ee.size()<eventCount);long ordinal=b.getLong(at+16),frame=b.getLong(at+24),texture=b.getLong(at+32),shade=b.getLong(at+40),address=b.getLong(at+48),shift=b.getLong(at+64);need(ordinal>previous&&frame>=refresh&&frame<=0xffffffffL&&texture>0&&texture<=aa.size()&&b.getLong(at+56)==1&&(shift==0||shift==1)&&b.getLong(at+72)==0&&b.getLong(at+80)==0&&b.getLong(at+88)==0);
    int[] c=new int[20];for(int i=0;i<20;i++)c[i]=b.getInt(at+96+i*4);Asset t=aa.get((int)texture-1);need(t.category==1&&t.address==address&&address==u(c[9])&&u(c[19])<=320&&u(c[3])<=10&&u(c[4])>=1&&u(c[4])<=1024);
    if(shift==1){need(shade>0&&shade<=aa.size());Asset s=aa.get((int)shade-1);need(s.category==2&&s.address==u(c[5]+(short)(c[10]>>>16)));}else need(shade==0);
    ee.add(new Event(frame,(int)texture-1,(int)shade-1,c));previous=ordinal;refresh=frame;
   }at+=(int)size;
  }need(at==input.length&&aa.size()==assetCount&&ee.size()==eventCount);assets=aa.toArray(new Asset[aa.size()]);events=ee.toArray(new Event[ee.size()]);
 }
 int count(){return events.length;}int assetCount(){return assets.length;}ByteBuffer asset(int id){return assets[id].data.asReadOnlyBuffer();}
 Samples samples(long expectedEpoch,long end,int page){
  need(expectedEpoch==epoch&&end>=0&&end<=0xffffffffL&&(page==0||page==1));int[] ids=new int[38400],offsets=new int[38400];long[] frames=new long[38400];Arrays.fill(ids,-1);Arrays.fill(offsets,-1);
  for(Event e:events){if(e.refresh>end)break;int[] c=e.command;int shift=c[3],uvshift=15,texture=c[9],step=c[11];if(c[6]!=0&&u(step)>0x1b000){need(shift>=2);shift-=2;uvshift=17;texture+=c[7];}
   texture=(texture+((c[13]&c[16])>>>uvshift))&~1;int dest=c[17]+((c[2]*(c[1]>>>14))<<1),vertical=c[18],mask=(c[4]<<15)-1;Asset source=assets[e.texture];
   for(int row=0;row<c[19];row++){vertical&=mask;long offset=u(texture+((vertical>>>uvshift)<<shift))-source.address;need(offset>=0&&offset<source.data.remaining());int index=source.data.get((int)offset)&255;
    if(index!=0){int asset=e.texture;if(e.shade>=0){asset=e.shade;offset=index*16;}
     for(int lane=0;lane<2;lane++){long cell=u((dest&~1)+lane)-(0x06000000L+page*0xa000L);if(cell>=0&&cell<38400){ids[(int)cell]=asset;offsets[(int)cell]=(int)offset;frames[(int)cell]=e.refresh;}}
    }dest+=c[2]<<1;vertical+=step;
   }
  }return new Samples(ids,offsets,frames);
 }
}

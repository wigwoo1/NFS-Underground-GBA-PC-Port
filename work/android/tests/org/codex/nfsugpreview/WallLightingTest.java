package org.codex.nfsugpreview;
import java.nio.file.*;import java.io.*;import java.util.*;
public class WallLightingTest {
 static int cases,real,skipped;static Path output;
 static void emit(NativeWallLighting light)throws Exception{if(light==null)return;for(int count:new int[]{1,240,3240,3839}){try(DataOutputStream out=new DataOutputStream(Files.newOutputStream(output.resolve(String.format("%04d.case",cases++))))){out.writeInt(count);for(double v:light.endpoints())out.writeDouble(v);for(int v:light.columns(count)){if(v<0||v>15)throw new AssertionError();out.writeInt(v);}}}}
 static void reject(double[] x,double[] z,double[] shade){try{NativeWallLighting.camera(x,z,shade,120,120);throw new AssertionError("Accepted bad shade");}catch(IllegalArgumentException expected){}}
 public static void main(String[] args)throws Exception{output=Paths.get(args[0]);Files.createDirectories(output);
  double[][][] examples={{{-100,100},{64,1024},{0,15}},{{100,-100},{1024,64},{15,0}},{{1,1.01},{1000,1000},{3,12}},{{1,2},{64,128},{0,15}},{{-100,100},{32,96},{0,15}},{{-100,100},{64,32767},{5,5}}};
  for(double[][] c:examples)emit(NativeWallLighting.camera(c[0],c[1],c[2],120,120));NativeWallLighting clipped=NativeWallLighting.camera(examples[4][0],examples[4][1],examples[4][2],120,120);double[] endpoints=clipped.endpoints();if(endpoints[0]!=120||endpoints[2]!=64||endpoints[4]!=7.5)throw new AssertionError("Near-plane interpolation");
  if(NativeWallLighting.camera(new double[]{0,1},new double[]{10,20},new double[]{0,15},120,120)!=null)throw new AssertionError("Behind wall");reject(new double[]{Double.NaN,1},new double[]{64,128},new double[]{0,15});reject(new double[]{0,1},new double[]{64,128},new double[]{-1,15});reject(new double[]{0,1},new double[]{64,32768},new double[]{0,15});
  Random random=new Random(177);for(int i=0;i<64;i++)emit(NativeWallLighting.camera(new double[]{random.nextDouble()*300-150,random.nextDouble()*300-150},new double[]{64+random.nextDouble()*3100,64+random.nextDouble()*3100},new double[]{random.nextInt(16),random.nextInt(16)},120,120));
  try(DirectoryStream<Path> files=Files.newDirectoryStream(Paths.get(args[1]),"*.nsp")){for(Path file:files){if(file.getFileName().toString().startsWith("bad-"))continue;NativeScenePacket packet=new NativeScenePacket(1,Files.readAllBytes(file));NativeWorldScene world=new NativeWorldScene(packet);for(int i=0;i<world.surfaceCount();i++)if(world.surface(i).lit){NativeWallLighting light;try{light=NativeWallLighting.surface(packet,world,i);}catch(IllegalArgumentException unsupported){skipped++;continue;}if(light==null){skipped++;continue;}emit(light);real++;}}}
  System.out.println("PASS_WALL_LIGHT_PREPARATION cases="+cases+" fixture_lit_walls="+real+" unsupported_or_behind="+skipped+" near_clip_and_rejections=true");
 }
}

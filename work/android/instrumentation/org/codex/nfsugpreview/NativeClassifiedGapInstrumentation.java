package org.codex.nfsugpreview;
import org.json.JSONArray;import org.json.JSONObject;import android.os.Bundle;import java.nio.file.Files;
/** Diagnostic JNI exists only in the isolated x86 test library. */
public final class NativeClassifiedGapInstrumentation extends NativeFirstGapInstrumentation {
 private boolean traceLifecycle,probeBackground,probeRejection,probeAssembly,probeBytes;
 private static native byte[] modelByteproof(long handle);
 private static native long[] modelAssembly(long handle);
 private static native long[] packetRejection(long handle);
 private static native long[] backgroundProbe(long handle);
 private static native byte[] backgroundProvenance(long handle);
 private static native long[] lifecycleTrace(long handle);
 private static native byte[] visibilityComparison(long handle);
 @Override public void onCreate(Bundle args){traceLifecycle=args!=null&&"true".equals(args.getString("lifecycleTrace","false"));probeBackground=args!=null&&"true".equals(args.getString("backgroundProbe","false"));probeRejection=args!=null&&"true".equals(args.getString("rejectionProbe","false"));probeAssembly=args!=null&&"true".equals(args.getString("assemblyProbe","false"));probeBytes=args!=null&&"true".equals(args.getString("byteProof","false"));super.onCreate(args);}
 @Override protected JSONObject captureContext(NativeCore core)throws Exception{
  if(probeBackground){long[] raw=backgroundProbe(core.ownerHandle());if(raw==null||raw.length!=64||raw[0]!=0x3147424eL||raw[1]!=1)throw new AssertionError("Background probe schema");for(int i=0;i<4;i++)if(raw[2+i]!=raw[52+i])throw new AssertionError("Probe advanced timing");JSONArray values=new JSONArray();for(long value:raw)values.put(value);byte[] provenance=backgroundProvenance(core.ownerHandle());if(provenance!=null)Files.write(file("-background-provenance.bin").toPath(),provenance);JSONObject out=new JSONObject();out.put("background_probe",values);if(probeRejection){long[] meta=packetRejection(core.ownerHandle());if(meta==null||meta.length!=153||meta[0]!=0x3152504eL||meta[1]!=1)throw new AssertionError("Packet rejection schema");JSONArray rejection=new JSONArray();for(long value:meta)rejection.put(value);out.put("packet_rejection",rejection);if(probeAssembly){long[] assembly=modelAssembly(core.ownerHandle());if(assembly==null||assembly.length!=48||assembly[0]!=0x31414d4eL||assembly[1]!=1||assembly[2]!=1)throw new AssertionError("Assembly probe incomplete");JSONArray data=new JSONArray();for(long value:assembly)data.put(value);out.put("model_assembly",data);if(probeBytes){byte[] proof=modelByteproof(core.ownerHandle());if(proof==null||proof.length<512)throw new AssertionError("Byteproof missing");Files.write(file("-model-byteproof.bin").toPath(),proof);out.put("model_byteproof_bytes",proof.length);}}}out.put("provenance_bytes",provenance==null?0:provenance.length);return out;}
  if(!traceLifecycle)return null;
  long[] raw=lifecycleTrace(core.ownerHandle());if(raw==null||raw.length<2||raw[0]<=0||raw[1]!=0||raw.length!=2+raw[0]*16)throw new AssertionError("Lifecycle trace incomplete");
  JSONArray rows=new JSONArray();for(int i=0;i<raw[0];i++){JSONArray row=new JSONArray();for(int j=0;j<16;j++)row.put(raw[2+i*16+j]);rows.put(row);}
  byte[] comparison=visibilityComparison(core.ownerHandle());if(comparison==null||comparison.length<256)throw new AssertionError("Comparison capture missing");Files.write(file("-visibility-comparison.bin").toPath(),comparison);
  JSONObject out=new JSONObject();out.put("events",rows);out.put("overflow",raw[1]);out.put("comparison_bytes",comparison.length);return out;
 }
 private static native long[] classifyWorld(long handle,long epoch,int serial,int begin,int end);
 @Override protected JSONArray classifyOwner(NativeCore core,NativeScenePacket packet){
  if(probeBackground)return null;
  long[] values=classifyWorld(core.ownerHandle(),packet.epoch,(int)packet.serial,(int)packet.beginRefresh,(int)packet.endRefresh);
  if(values==null||values.length!=32)throw new AssertionError("Diagnostic classification unavailable");
  JSONArray result=new JSONArray();for(long value:values)result.put(value);return result;
 }
}

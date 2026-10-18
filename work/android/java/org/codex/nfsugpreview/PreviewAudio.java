package org.codex.nfsugpreview;
import android.media.*;
import java.util.Arrays;
import java.util.concurrent.*;
final class PreviewAudio implements AutoCloseable {
 private final ArrayBlockingQueue<short[]> queue=new ArrayBlockingQueue<>(8);
 private volatile boolean enabled,closed;
 volatile int droppedChunks;
 volatile String error;
 private final Thread thread;
 PreviewAudio(){thread=new Thread(this::run,"NFSUG-Audio");thread.start();}
 void enabled(boolean value){enabled=value;if(!value)queue.clear();}
 void offer(short[] samples,int frames){
  if(enabled&&frames>0&&!queue.offer(Arrays.copyOf(samples,frames*2)))droppedChunks++;
 }
 private void run(){
  AudioTrack track=null;
  try{
   int minimum=AudioTrack.getMinBufferSize(44100,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT);
   if(minimum<=0)throw new IllegalStateException("Audio format unavailable");
   track=new AudioTrack.Builder().setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
    .setAudioFormat(new AudioFormat.Builder().setSampleRate(44100).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
    .setBufferSizeInBytes(Math.max(minimum,8192)).setTransferMode(AudioTrack.MODE_STREAM).build();
   boolean playing=false;
   while(!closed){
    if(!enabled){if(playing){track.pause();track.flush();playing=false;}Thread.sleep(10);continue;}
    if(!playing){track.play();playing=true;}
    short[] samples=queue.poll(20,TimeUnit.MILLISECONDS);if(samples==null)continue;
    int offset=0;
    while(enabled&&!closed&&offset<samples.length){
     int written=track.write(samples,offset,samples.length-offset,AudioTrack.WRITE_BLOCKING);
     if(written<=0)throw new IllegalStateException("Audio playback failed: "+written);
     offset+=written;
    }
   }
  }catch(InterruptedException expected){Thread.currentThread().interrupt();}
   catch(Exception e){error=e.getMessage();}
  finally{if(track!=null){try{track.pause();track.flush();}catch(Exception ignored){}track.release();}}
 }
 public void close(){closed=true;enabled=false;queue.clear();thread.interrupt();}
}

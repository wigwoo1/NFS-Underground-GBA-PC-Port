package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import java.io.*;
/** Instrumentation-only Activity; never reads or writes normal game saves. */
public final class LiveTestActivity extends Activity {
 static String TEST_ROOT="live-test-private";
 GameSession session;FrameView view;volatile String status="";
 @Override public void onCreate(Bundle state){super.onCreate(state);File root=new File(getFilesDir(),TEST_ROOT);session=new GameSession(new PrivateStore(root),message->{status=message;android.util.Log.i("NFSUGLiveTest",message);});session.profile.enabled=true;view=new FrameView(this,session);view.setPreserveEGLContextOnPause(false);setContentView(view);session.keys.set(1);session.nativeDisplay(true);session.open();}
 @Override public void onResume(){super.onResume();view.onResume();session.active(true);}
 @Override public void onPause(){session.active(false);view.onPause();super.onPause();}
 @Override public void onDestroy(){session.shutdown();super.onDestroy();}
}

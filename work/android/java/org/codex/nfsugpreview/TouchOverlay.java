package org.codex.nfsugpreview;

import android.content.Context;

import android.graphics.*;

import android.util.SparseIntArray;

import android.view.*;

final class TouchOverlay extends View {

 private final GameSession session;

 private final SparseIntArray pointers=new SparseIntArray();

 private final Paint paint=new Paint(3);

 TouchOverlay(Context c,GameSession s){super(c);session=s;setContentDescription("D-pad, A, B, Start and Select controls");}

 void clear(){pointers.clear();session.keys.set(0);invalidate();}

 private float unit(){return Math.min(getWidth()*.075f,getHeight()*.15f);}

 private int hit(float x,float y){

  float u=unit(),dx=(x-getWidth()*.14f)/u,dy=(y-getHeight()*.66f)/u;

  if(Math.abs(dx)<1.5&&Math.abs(dy)<1.5){

   int bits=0;if(dx>.35)bits|=16;if(dx<-.35)bits|=32;if(dy>.35)bits|=128;if(dy<-.35)bits|=64;return bits;

  }

  if(Math.hypot(x-getWidth()*.88f,y-getHeight()*.62f)<u)return 1;

  if(Math.hypot(x-getWidth()*.76f,y-getHeight()*.78f)<u)return 2;

  if(Math.abs(x-getWidth()*.43f)<u&&Math.abs(y-getHeight()*.88f)<u*.45)return 4;

  if(Math.abs(x-getWidth()*.57f)<u&&Math.abs(y-getHeight()*.88f)<u*.45)return 8;

  return 0;

 }

 @Override public boolean onTouchEvent(MotionEvent e){

  if(!isEnabled()){clear();return true;}

  int action=e.getActionMasked();

  // ACTION_DOWN starts a new gesture, even if an earlier stream was interrupted.
  if(action==MotionEvent.ACTION_DOWN)pointers.clear();

  if(action==MotionEvent.ACTION_CANCEL){clear();return true;}

  int released=action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP?e.getPointerId(e.getActionIndex()):-1;

  for(int i=0;i<e.getPointerCount();i++){

   int id=e.getPointerId(i);if(id==released)pointers.delete(id);else pointers.put(id,hit(e.getX(i),e.getY(i)));

  }

  int bits=0;for(int i=0;i<pointers.size();i++)bits|=pointers.valueAt(i);

  if((bits&48)==48)bits&=~48;if((bits&192)==192)bits&=~192;

  session.keys.set(bits);invalidate();return true;

 }

 private void button(Canvas c,float x,float y,String label,int bit){

  float u=unit();paint.setColor((session.keys.get()&bit)!=0?0xCC48A8FF:0x88505050);c.drawCircle(x,y,u,paint);

  paint.setColor(Color.WHITE);paint.setTextSize(u*.65f);paint.setTextAlign(Paint.Align.CENTER);c.drawText(label,x,y+u*.22f,paint);

 }

 @Override protected void onDraw(Canvas c){

  float w=getWidth(),h=getHeight(),u=unit();paint.setColor(0x88606060);

  c.drawRoundRect(w*.14f-u*.5f,h*.66f-u*1.5f,w*.14f+u*.5f,h*.66f+u*1.5f,8,8,paint);

  c.drawRoundRect(w*.14f-u*1.5f,h*.66f-u*.5f,w*.14f+u*1.5f,h*.66f+u*.5f,8,8,paint);

  button(c,w*.88f,h*.62f,"A",1);button(c,w*.76f,h*.78f,"B",2);

  paint.setTextSize(u*.45f);paint.setTextAlign(Paint.Align.CENTER);paint.setColor(Color.WHITE);

  c.drawText("SELECT",w*.43f,h*.88f,paint);c.drawText("START",w*.57f,h*.88f,paint);

 }

}


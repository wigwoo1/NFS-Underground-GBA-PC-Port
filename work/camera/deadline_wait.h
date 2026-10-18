/* Opt-in presentation scheduler experiment. Original clocks remain unchanged. */
static HANDLE nf_deadline_timer;
static unsigned nf_deadline_waits;
static int nf_deadline_wait_init(void){
 if(!getenv("NF_PRECISE_WAIT")&&!getenv("NF_PRESENT_PHASE_US"))return 1;
 HANDLE(WINAPI*create)(LPSECURITY_ATTRIBUTES,LPCSTR,DWORD,DWORD)=(void*)GetProcAddress(GetModuleHandleA("kernel32.dll"),"CreateWaitableTimerExA");
 if(!create)return 0;
 nf_deadline_timer=create(NULL,NULL,2,TIMER_ALL_ACCESS);
 return nf_deadline_timer!=NULL;
}
static int nf_deadline_wait_until(uint64_t deadline){
 uint64_t now=elapsed_ns();if(deadline<=now)return 1;
 if(!nf_deadline_timer){if(deadline>now+2000000)Sleep(1);else SwitchToThread();return 1;}
 /* Sleep most of the interval; bounded final spin avoids coarse timer jitter. */
 if(deadline>now+500000){
  LARGE_INTEGER due;due.QuadPart=-(LONGLONG)((deadline-now-500000+99)/100);
  if(!SetWaitableTimer(nf_deadline_timer,&due,0,NULL,NULL,FALSE)||WaitForSingleObject(nf_deadline_timer,1000)!=WAIT_OBJECT_0)return 0;
  nf_deadline_waits++;
 }
 while(elapsed_ns()<deadline)YieldProcessor();
 return 1;
}

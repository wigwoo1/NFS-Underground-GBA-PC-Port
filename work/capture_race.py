exec(open('work/run_probe.py').read().split('if len(sys.argv)>1:')[0])
assert d.nf_state(str(ROOT/'race.state').encode(),0)
d.nf_capture.argtypes=[C.c_char_p]
d.nf_capture(str(ROOT/'spans.bin').encode())
changes=[];prev=None;rows=[]
for i in range(600):
 d.nf_frame(1)
 p=C.string_at(d.nf_pixels(),240*160*4)
 h=hashlib.sha256(p).hexdigest()
 if prev!=h:changes.append(i)
 prev=h
 rows.append({'vblank':i,'dispcnt':d.nf_read(0x4000000,2),'sha256':h})
d.nf_capture(None)
(ROOT/'cadence.json').write_text(json.dumps({'frames':rows,'changed_frames':changes},indent=2))
shot('race-accelerating')
d.nf_state(str(ROOT/'driving.state').encode(),1)
d.nf_dump(str(ROOT/'driving-iwram.bin').encode(),0x03000000,0x8000)
d.nf_dump(str(ROOT/'driving-ewram.bin').encode(),0x02000000,0x40000)
print('changed',len(changes),'intervals',__import__('collections').Counter(b-a for a,b in zip(changes,changes[1:])))
d.nf_close()

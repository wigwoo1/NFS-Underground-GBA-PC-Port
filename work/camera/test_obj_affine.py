exec(open('work/camera/test_obj_image.py').read())
aff=d.nf_obj_affine_image;aff.argtypes=api.argtypes[:8]+[C.c_void_p]+api.argtypes[8:]
for n in range(96):
 w,h=sizes[n%3][(n//3)%4];a=((n%3)<<14)|256|(512 if n%2 else 0);b=((n//3)%4)<<14;c=512;v=rng.randbytes(0x18000);pal=rng.randbytes(1024);src=(C.c_uint32*4096)();dims=(C.c_uint*2)();assert api(v,len(v),pal,len(pal),a&~0x300,b,c,68,src,4096,dims)
 coeff=([256,0,0,256],[0,-256,256,0],[128,32,-64,512],[-256,0,0,256])[n%4];m=(C.c_int16*4)(*coeff);out=(C.c_uint32*16384)();assert aff(v,len(v),pal,len(pal),a,b,c,68,m,out,16384,dims);dw,dh=dims
 for y in range(dh):
  for x in range(dw):
   u=x-dw//2;z=y-dh//2;sx=(coeff[0]*u+coeff[1]*z)//256+w//2;sy=(coeff[2]*u+coeff[3]*z)//256+h//2;expected=src[sy*w+sx] if 0<=sx<w and 0<=sy<h else 0;assert out[y*dw+x]==expected
out=(C.c_uint32*16384)(*([0x12345678]*16384));dims=(C.c_uint*2)(123,456);assert not aff(v,len(v),pal,len(pal),a,b,c,68,m,out,1,dims) and list(dims)==[123,456] and out[0]==0x12345678
r=dict(result='PASS',cases=96,atomic_rejections=1,scope='Signed8.8 affine inverse placement/double-size/clipped transparency analytic oracle; originalhardwarecompositeverificationpending');(p/'obj-affine-tests.json').write_text(json.dumps(r,indent=2));print(r)

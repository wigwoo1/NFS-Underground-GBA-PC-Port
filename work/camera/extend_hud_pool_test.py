from pathlib import Path
p=Path('work/camera/hud_row_pool_test.c');s=p.read_text();needle=' free(data);free(ref);free(out);return 0;}'
assert needle in s
s=s.replace(needle,''' memset(data,0,n);for(unsigned i=0;i<160;i++){NFHudLayerRow*r=(NFHudLayerRow*)data+i;r->refresh=99;r->row=i;r->palette[0]=(uint8_t)i;r->oam[1]=(uint8_t)(159-i);}NFHudRowPool*worst=nf_hud_pool_create(data,n,9);CHECK(worst&&worst->count==160);CHECK(nf_hud_pool_expand(worst,worst->bytes,9,out,n)&&!memcmp(data,out,n));printf("HUD_POOL_WORST_CASE rows=160 unique=160 exact=PASS bytes=%zu\\n",worst->bytes);free(worst);
 for(unsigned i=0;i<160;i++){NFHudLayerRow*r=(NFHudLayerRow*)data+i;memset(r->obj_vram,0,NF_HUD_POOL_PAYLOAD);}NFHudRowPool*one=nf_hud_pool_create(data,n,9);CHECK(one&&one->count==1);CHECK(nf_hud_pool_expand(one,one->bytes,9,out,n)&&!memcmp(data,out,n));printf("HUD_POOL_IDENTICAL_PAYLOAD rows=160 unique=1 exact=PASS bytes=%zu\\n",one->bytes);free(one);
 free(data);free(ref);free(out);return 0;}''');p.write_text(s)

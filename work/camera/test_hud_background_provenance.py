import itertools,json,sys
from pathlib import Path
from hud_background_provenance import hud_background_passthrough
# Independent evaluation of shader's no-visible-OBJ branch with distinct RGB.
def shader_background(control,obj,text,text_enabled,mode,first_bg,second_bd,brightness):
    b=[37,111,203];d=[211,53,17]
    has_obj=obj>127 and control&16;has_bg=bool(control&4)
    if text_enabled and text>127:b=[19,89,157]
    active_mode=mode if control&32 else 0
    if active_mode in (2,3) and first_bg:
        y=min(brightness,16)
        b=[c+(255-c)*y//16 if active_mode==2 else (c-c*y//16 if i==0 else c*(16-y)//16) for i,c in enumerate(b)]
    if has_obj:return [251,3,47]
    if not has_bg:return d
    if active_mode==1 and first_bg and second_bd:return [(c*7+v*9)//16 for c,v in zip(b,d)]
    return b
accepted=0;total=0
for control,obj,text,text_enabled,mode,first_bg,second_bd,brightness in itertools.product(range(64),(0,255),(0,255),(0,1),range(4),(0,1),(0,1),(0,1,15,16,31)):
    blend=(mode<<6)|(first_bg<<2)|(second_bd<<13)
    result=hud_background_passthrough(control,obj,text,text_enabled,blend,brightness);total+=1
    if result:
        accepted+=1
        assert shader_background(control,obj,text,text_enabled,mode,first_bg,second_bd,brightness)==[37,111,203]
assert accepted>0
out=dict(result='PASS_CONSERVATIVE_HUD_BACKGROUND_GATE',cases=total,accepted=accepted,scope='Independent CPU shader-branch oracle with distinct background/backdrop/text/OBJ colors. No false pass-through in enumerated modes/windows/brightness; conservative rejects allowed. Not GLSL execution, world occlusion or live provenance proof.')
Path(sys.argv[1]).write_text(json.dumps(out,indent=2));print(out)

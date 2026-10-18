from pathlib import Path
p=Path('work/camera');s=(p/'owned_d3d_hud_copy_candidate.c').read_text()
s=s.replace('static DWORD owner;','static DWORD owner;') if False else s
pos=s.index('static uint64_t draws')
s=s[:pos]+'static ID3D11PixelShader*hud_ps;static ID3D11Buffer*hud_constants;static int hud_active;static unsigned hud_ids[4];\n'+s[pos:]
s=s.replace('DROP(ID3D11Buffer,constants);','DROP(ID3D11PixelShader,hud_ps);DROP(ID3D11Buffer,hud_constants);hud_active=0;DROP(ID3D11Buffer,constants);')
s=s.replace('ID3D11DeviceContext_Draw(ctx,count,0);','if(hud_active){ID3D11ShaderResourceView*inputs[4];for(unsigned j=0;j<4;j++)inputs[j]=views[hud_ids[j]];ID3D11DeviceContext_PSSetShader(ctx,hud_ps,NULL,0);ID3D11DeviceContext_PSSetConstantBuffers(ctx,0,1,&hud_constants);ID3D11DeviceContext_PSSetShaderResources(ctx,0,4,inputs);}ID3D11DeviceContext_Draw(ctx,count,0);')
s+='''
__declspec(dllexport) int nf_d3d_hud_shader(const void*code,size_t bytes){
 if(!valid()||!code||!bytes||hud_ps)return 1;
 if(FAILED(ID3D11Device_CreatePixelShader(dev,code,bytes,NULL,&hud_ps)))return 2;
 D3D11_BUFFER_DESC bd;memset(&bd,0,sizeof(bd));bd.ByteWidth=96;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
 if(FAILED(ID3D11Device_CreateBuffer(dev,&bd,NULL,&hud_constants))){ID3D11PixelShader_Release(hud_ps);hud_ps=NULL;return 3;}return 0;
}
__declspec(dllexport) int nf_d3d_hud_draw(const float*vertices,unsigned count,const unsigned*ids,const void*parameters,const float*config,const int*rect){
 if(!valid()||!hud_ps||!ids||!parameters||hud_active)return 1;
 for(unsigned j=0;j<4;j++){if(ids[j]>=4096||!views[ids[j]])return 1;hud_ids[j]=ids[j];}
 ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)hud_constants,0,NULL,parameters,0,0);
 hud_active=1;int result=nf_d3d_draw(vertices,count,0,0,0,config,rect);hud_active=0;return result;
}
'''
(p/'owned_d3d_full_scene_candidate.c').write_text(s)
import json
ops=json.loads((p/'prototype-runs/normalized-source-gpu-packets.json').read_text())['ops']
print([o for o in ops if o['op']=='copy_render_target'][:2]);print(next(o for o in ops if o['op']=='draw_triangles' and o['program'])['uniforms'])

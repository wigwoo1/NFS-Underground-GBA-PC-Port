from pathlib import Path
p=Path('work/camera');s=(p/'owned-d3d-matrix-load-candidate.c').read_text()
s+='''
/* HUD background snapshot: native GPU copy, with top-down D3D coordinates. */
__declspec(dllexport) int nf_d3d_copy_target(unsigned id){
 if(!valid()||!id||id>=4096)return 1;
 D3D11_TEXTURE2D_DESC td;ID3D11Texture2D_GetDesc(target,&td);td.BindFlags=D3D11_BIND_SHADER_RESOURCE;
 ID3D11Texture2D*next=NULL;ID3D11ShaderResourceView*view=NULL;
 if(FAILED(ID3D11Device_CreateTexture2D(dev,&td,NULL,&next)))return 2;
 if(FAILED(ID3D11Device_CreateShaderResourceView(dev,(ID3D11Resource*)next,NULL,&view))){ID3D11Texture2D_Release(next);return 3;}
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)next,(ID3D11Resource*)target);
 if(views[id])ID3D11ShaderResourceView_Release(views[id]);
 if(textures[id]){ID3D11Texture2D_Release(textures[id]);live_textures--;}
 textures[id]=next;views[id]=view;live_textures++;return 0;
}
'''
(p/'owned_d3d_hud_copy_candidate.c').write_text(s)

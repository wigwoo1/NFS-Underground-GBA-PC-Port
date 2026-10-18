from pathlib import Path
p=Path('work/camera');s=(p/'owned_d3d_full_scene_candidate.c').read_text().replace('#include <d3d11.h>','#include <d3d11.h>\n#include <dxgi.h>')
s=s.replace('static uint64_t draws','static IDXGISwapChain*chain;\nstatic uint64_t draws').replace('DROP(ID3D11Buffer,constants);','DROP(IDXGISwapChain,chain);DROP(ID3D11Buffer,constants);')
s+='''
__declspec(dllexport) int nf_d3d_window(HWND window){
 if(!valid()||!IsWindow(window)||chain)return 1;
 IDXGIDevice*dx=NULL;IDXGIAdapter*adapter=NULL;IDXGIFactory*factory=NULL;
 HRESULT h=ID3D11Device_QueryInterface(dev,&IID_IDXGIDevice,(void**)&dx);
 if(SUCCEEDED(h))h=IDXGIDevice_GetAdapter(dx,&adapter);
 if(SUCCEEDED(h))h=IDXGIAdapter_GetParent(adapter,&IID_IDXGIFactory,(void**)&factory);
 if(SUCCEEDED(h)){
 DXGI_SWAP_CHAIN_DESC d;memset(&d,0,sizeof(d));d.BufferDesc.Width=3840;d.BufferDesc.Height=2160;d.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.SampleDesc.Count=1;d.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;d.BufferCount=2;d.OutputWindow=window;d.Windowed=TRUE;d.SwapEffect=DXGI_SWAP_EFFECT_DISCARD;
 h=IDXGIFactory_CreateSwapChain(factory,(IUnknown*)dev,&d,&chain);
 if(SUCCEEDED(h))IDXGIFactory_MakeWindowAssociation(factory,window,DXGI_MWA_NO_ALT_ENTER);
 }
 if(factory)IDXGIFactory_Release(factory);if(adapter)IDXGIAdapter_Release(adapter);if(dx)IDXGIDevice_Release(dx);
 return FAILED(h)?2:0;
}
__declspec(dllexport) int nf_d3d_present(void){
 if(!valid()||!chain)return 1;ID3D11Texture2D*back=NULL;
 if(FAILED(IDXGISwapChain_GetBuffer(chain,0,&IID_ID3D11Texture2D,(void**)&back)))return 2;
 ID3D11DeviceContext_CopyResource(ctx,(ID3D11Resource*)back,(ID3D11Resource*)target);ID3D11Texture2D_Release(back);
 HRESULT h=IDXGISwapChain_Present(chain,1,0);return h==S_OK?0:(h==DXGI_STATUS_OCCLUDED?3:4);
}
'''
(p/'owned_d3d_window_candidate.c').write_text(s)
s=(p/'test_d3d_full_scene_candidate.py').read_text().replace('owned-d3d-full-scene-candidate.dll','owned-d3d-window-candidate.dll').replace('d3d-full-scene-','d3d-window-scene-')
s=s.replace('status=d.nf_d3d_open();',"user=C.WinDLL('user32',use_last_error=True);user.CreateWindowExW.argtypes=[C.c_uint,C.c_wchar_p,C.c_wchar_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_int,P,P,P,P];user.CreateWindowExW.restype=P;user.DestroyWindow.argtypes=[P];user.ShowWindow.argtypes=[P,C.c_int];window=user.CreateWindowExW(0,'STATIC','NFSUG native D3D scene diagnostic',0x00cf0000,100,100,960,540,None,None,None,None);assert window;user.ShowWindow(window,5)\nstatus=d.nf_d3d_open();")
s=s.replace('textures={};frames=[];',"d.nf_d3d_window.argtypes=[P];assert d.nf_d3d_window(window)==0\ntextures={};frames=[];")
s=s.replace("  elif kind=='end_frame':", "  elif kind=='end_frame':\n   assert d.nf_d3d_present()==0")
s=s.replace('r=dict(result=', 'user.DestroyWindow(window)\nr=dict(result=')
(p/'test_d3d_window_scene_candidate.py').write_text(s)

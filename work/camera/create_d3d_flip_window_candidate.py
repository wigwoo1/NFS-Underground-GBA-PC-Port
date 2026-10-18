from pathlib import Path
p=Path('work/camera');s=(p/'owned_d3d_window_pump_candidate.c').read_text().replace('d.SwapEffect=DXGI_SWAP_EFFECT_DISCARD','d.SwapEffect=(DXGI_SWAP_EFFECT)4')
(p/'owned_d3d_flip_window_candidate.c').write_text(s)
s=(p/'test_d3d_window_pump_scene_candidate.py').read_text().replace('owned-d3d-window-pump-candidate.dll','owned-d3d-flip-window-candidate.dll').replace('d3d-window-pump-scene-','d3d-flip-window-scene-')
s=s.replace('"""Actual captured source-world/sky D3D component. HUD deliberately pending."""','"""Full-scene flip-model D3D component; sandbox presentation is not scanout proof."""')
(p/'test_d3d_flip_window_scene_candidate.py').write_text(s)

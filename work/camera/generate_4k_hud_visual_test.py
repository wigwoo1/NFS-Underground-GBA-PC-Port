from pathlib import Path
p=Path('work/camera');s=(p/'test_segmented_4k_gpu_parity.py').read_text().replace('owned-gpu-segmented-4k-candidate.dll','owned-gpu-segmented-4k-hud-reuse-candidate.dll')
s=s.replace(" assert len(set(images))>1"," stats=(C.c_uint64*2)();assert gpu.nf_hud_visual_cache_stats(stats);print('HUD cache hits/misses',list(stats))\n assert stats[0]>0,'Reuse path not exercised'\n assert len(set(images))>1")
(p/'test_4k_hud_visual_reuse.py').write_text(s)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/4k-hud-visual-reuse-20261008');cp.mkdir(exist_ok=True)

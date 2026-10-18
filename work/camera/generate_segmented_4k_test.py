from pathlib import Path
p=Path('work/camera');s=(p/'test_segmented_original_gpu_parity.py').read_text().replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-4k-candidate.dll')
(p/'test_segmented_4k_gpu_parity.py').write_text(s)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-4k-20261008');cp.mkdir(exist_ok=True)

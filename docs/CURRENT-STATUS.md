# Current project status — 2026-10-22

Original GBA gameplay in mGBA is the permanent architecture. A native gameplay rewrite is outside scope. Finish the replacement renderer before texture/music enhancements.

Overall completion is roughly 40%, a subjective planning estimate superseding historical percentages. Full-scene 60fps, true widescreen, sustained visible fidelity, physical Xbox testing, replacement textures/music and Android renderer qualification remain incomplete.

An isolated world-only renderer passed muted saved-race tests of 600 standard, 600 Select and 1800 diverse original updates, preserving expected PCM and original timing. Those runs had zero low-resolution recovery events but still repeated native timestamps. Two boot smoke tests passed 600 updates; they stayed in opening screens and do not prove complete boot-to-race behavior. Visible fidelity and audible playback remain unqualified.

A scheduled-clock-anchor experiment removed monotonic clock holds but increased missing-scene recovery; it was rejected and is not in the offered local preview. Timing/camera investigation continues.

Public downloads remain unchanged. The newest local experimental preview has not been published: its complete corresponding-source and ROM-free package audit is pending. Isolated source checkpoints have not all been integrated into the maintained public work tree. This update is partial synchronization, not a claim that GitHub contains all current experiments.

The historical docs/STATUS.md and SOURCE-MANIFEST.json remain unchanged. This current-status note supersedes historical project-direction and percentage statements. The muted-test helper is newly included; no ROMs, saves, captures or replacement artwork are included.

## Queue-drop correction qualification

An isolated bounded raw-input FIFO candidate raises only its slot limit from two to eight, retaining the 128 MiB reservation budget and original game timing. Prepared-result FIFO behavior is unchanged. Standard 600, Select 600 and diverse 1800-update muted replays had zero rejected input snapshots and zero low-resolution fallbacks after native startup. Standard framebuffer and all three PCM checks passed. Repeated targets remain (7/13/37); this is not full-scene 60fps qualification.

Additional 600-update reload, renderer-toggle and pause tests passed timing and ownership checks, with zero input rejections and peak reserved bytes 65,071,876. These lifecycle tests did not compare PCM. The candidate is not promoted to downloads. A separate Select scene capture failure and clock jitter remain under investigation.

# Preview downloads

Windows: the existing verified EXE `ba85daea834c50e6f405a985207fa09c8f87c034650d46dfc02dcbd70446466b` and core `cf66b6edbd86d8cd1261cf59a4e529f9aac821ffe442e4f01dd46de8bfb83f44`, repackaged with license notices and a ROM-free boot launcher. The supplied race checkpoint and its launcher are omitted. Extract the ZIP to a local folder and supply your own GBA ROM.

Android: current production-preview APK `a5a13575e304d314d6e03ce24bd64974d88d29c5a67ffab448103bbb277b05e8`, including native-scene/background reuse work. Emulator/component validation is not physical Android/full-race/60-fps acceptance. The preview APK certificate is included as usual, but its private signing key is not.

The Windows renderer/history diagnostic source is newer than the downloadable playable Windows binary. It is not promoted as a new smooth-motion build. Original game timing is retained. Audio/Intel pacing, tearing and complete-game quality gates remain unresolved. No ROM, save, remastered textures, soundtrack replacements or private keys are bundled.

[SHA256SUMS](SHA256SUMS) covers both downloads. ZIP CRCs and all packaged Windows member hashes were independently checked with Python zipfile; APK ZIP integrity and member exclusions were checked too. This was packaging verification, not a new complete-game test.

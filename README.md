# NFS Underground GBA — PC and Android port project

Experimental source-driven native rendering for **Need for Speed: Underground for Game Boy Advance**. The project still uses **mGBA to execute the original game logic**; complete-scene smooth 60-fps gameplay and a complete native replacement of game code are not verified.

## Downloads

- [Windows x64 native-renderer preview](builds/NFSUG-Windows-Native-Renderer-Preview-20261018.zip?raw=1): extract the entire ZIP locally and drag your own compatible GBA ROM onto `START - Game From Boot.cmd`.
- [Android preview candidate](builds/NFSUG-Android-Core-Preview-20261017.apk?raw=1): install the APK, then select your own ROM in the app. Physical-device/full-race acceptance remains open.
- [Build notes and SHA-256 checksums](builds/README.md). These are previews, not finished releases.

No ROM, save state, battery save, original music, extracted artwork, or signing private key is included. Keep your existing saves separately.

## Current code

- `work/pc`: owned snapshots, native GPU renderer, source-time sampling, Windows host and tests.
- `work/android`: Android host/JNI, GLES integration and touch controls.
- `work/camera`: source reconstruction components and historical research/test tools.
- `build-inputs/windows-qualified-core`: corresponding source stage for the Windows playable core.
- `build-inputs/history-provenance-core`: current isolated retained-history diagnostic core.
- `vendor/mgba`: patched mGBA dependency source and original licenses.
- [Current checkpoint](docs/STATUS.md), [roadmap](PROJECT-PLAN.md), and [publication details](PUBLICATION.md).

The latest retained-history/source-time work is diagnostic and is not enabled in the downloadable Windows preview. Menus/unsupported states can use the original framebuffer. Audio queue underruns, Intel-PC pacing, physical tearing, complete-game flow and full-scene motion remain open. A native 4K render target does not mean original textures have become 4K artwork.

## Planned settings

Graphics: **Original**, **Re-imagined** (new AI-generated 4K artwork), **Remastered** (SUPIR upscales). Music: **Original** / **Remastered** using user-provided MP3s after track identification, plus a **Sound Test** menu. These options and complete replacement packs are not implemented by this snapshot.

## Building and testing

This is a source snapshot of an existing development workspace. Some historical research scripts refer to local fixture folders or tools; ROM-derived fixtures and private checkpoints are deliberately absent. Personal workspace prefixes have been replaced with `C:/NFSUG-Workspace`/equivalent. Build provenance is provided under `docs/build-provenance`; local paths/toolchain settings must be adapted before rebuilding. A clean build from this public checkout has not yet been independently qualified. Published binaries match their existing verified checkpoint hashes.

## Licensing

mGBA and bundled third-party code retain their original licenses/notices. Windows downloads include mGBA and runtime notices. No new project-wide license has been chosen for project-specific code. No rights to Electronic Arts, Nintendo, or other game content are granted.

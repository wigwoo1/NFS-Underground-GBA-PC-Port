# NFS Underground GBA — PC and Android port project

Work in progress on a source-driven native renderer for **Need for Speed: Underground for Game Boy Advance**, with a Windows preview and an Android preview.

The current project still uses **mGBA to execute the original game logic**. It is not a completed replacement of the game code, and complete-scene smooth 60-fps gameplay has not been verified. A 4K render target is separate from high-resolution replacement artwork.

## Publication status

The initial source export and ROM-free build packages are being prepared. This repository bootstrap does not yet contain those files. Follow-up commits will add the checked source snapshot, build packages, checksums, and detailed limitations.

## Required game data

Supply your own compatible GBA ROM. No commercial ROM, save states, battery saves, original soundtrack files, or extracted game artwork are included in this publication.

## Planned features

- Native PC rendering with original game timing, complete-scene motion reconstruction, and Xbox controller support.
- Graphics options: **Original**, **Re-imagined** (new AI-generated 4K artwork), and **Remastered** (SUPIR upscales of original textures).
- Music options: **Original** and **Remastered**, using replacement MP3s provided by the user; a complete track inventory and Sound Test menu are planned.
- Android APK with touch D-pad, A, B, Start, and Select controls.

These are project goals, not claims that every feature is implemented.

## Third-party code

mGBA and other third-party components retain their respective licenses. Corresponding source and license notices will accompany the source/build export. Publication does not grant rights to Nintendo, Electronic Arts, or other third-party game content.

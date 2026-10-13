# Third-party components

The Windows distribution bundles CPython, Pygame-ce/SDL and their runtime dependencies via PyInstaller. Their license files shipped with the dependencies apply. Development uses pytest, Ruff, mypy and PyInstaller.

- [Pygame-ce project and license](https://pypi.org/project/pygame-ce/) — LGPL-2.1-or-later.
- [Python license](https://docs.python.org/3/license.html).
- [PyInstaller license and bundling exception](https://pyinstaller.org/en/stable/license.html).

New class/enemy/weapon/forest art is original built-in ImageGen output preserved under `art_sources/`, processed into runtime PNGs by project-authored Pillow code. Terrain textures, effect prototypes, menu materials and sound cues are original project work. No external art pack or extracted Warcraft assets are bundled. See `docs/ASSET_CREDITS.md` for the acquisition/provenance record. Warcraft setting/class/ability names belong to their respective rights holders. This is the user's private educational non-commercial fan project.

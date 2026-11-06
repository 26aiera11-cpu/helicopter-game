# GitHub Pages deployment size investigation

Date: 2026-11-06 (KST)

## Incident

The Pages build for commit `8e5f89ba8ad9980e562b42d11f9dda9004a4c923` completed, but the deploy job did not publish the artifact. The deploy log remained in `syncing_files` until the 10-minute action timeout, then canceled the deployment.

- Workflow run: https://github.com/26aiera11-cpu/helicopter-game/actions/runs/42156429739
- Build job: successful
- Deploy job: failed (timeout while syncing files)
- Uploaded Pages artifact: 670,578,724 bytes

## Repository size breakdown

The recursive Git tree at the failed deployment commit reported:

| Path | Files | Size |
| --- | ---: | ---: |
| `docs/` | 3,080 | 554,886,786 bytes |
| `dist/` | 2 | 110,512,786 bytes |
| `assets/` | 92 | 39,801,649 bytes |
| `backups/` | 3 | 21,229,480 bytes |
| `index.html` | 1 | 18,718,309 bytes |
| `heli_trio_clean_selection-1.html` | 1 | 11,810,891 bytes |
| `tests/` | 124 | 1,014,368 bytes |
| `DEVELOPMENT_LOG.md` | 1 | 417,524 bytes |
| `scripts/` | 3 | 25,188 bytes |

The public game needs the root `index.html` and `assets/`. Development evidence, test bundles, backups, and the alternate HTML are not runtime dependencies of the Pages game.

## Pages configuration change

Added root `_config.yml` to exclude only non-runtime materials from the Jekyll Pages output:

- `docs/`
- `dist/`
- `backups/`
- `tests/`
- `scripts/`
- `DEVELOPMENT_LOG.md`
- `heli_trio_clean_selection-1.html`

These files remain in GitHub. No source files or game assets are deleted or moved by this Pages-only configuration.

## Required verification

After this configuration reaches `main`, verify that:

1. The Pages build job succeeds.
2. The Pages artifact is materially smaller (expected to be near the game runtime size, not hundreds of MB).
3. The Pages deploy job finishes with `success`.
4. The public URL serves the new root `index.html` and required assets, including both volcano WAV files.
5. The Galaxy/browser game smoke test still passes.

Do not claim deployment success until the Pages deploy job succeeds and the public URL is checked.

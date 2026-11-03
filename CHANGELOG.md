# Changelog

All notable changes to this project are listed here. Versions are dated by month, like `v2026.11`.

## v2026.11 · November 2026

A full rebuild, from a single notebook into a tested, reproducible analysis.

### Fixed

- The scatter plot of artist and track popularity had its axes swapped: the axis labelled "Artist Popularity" showed
  track popularity, and the other way round
- The "top 10 artists" counted rows in the file, not popularity. Nirvana was 5th only because 70 of its 91 tracks come
  from one deluxe album
- The "tracks released per year" chart was described as music production, but it counts what was collected. Its 1991
  spike is that same deluxe album
- Popularity was described as "normal-like". It isn't: 442 songs score exactly 0 and most score 60 to 79
- The title said 2009 to 2025 and promised audio features. The songs go back to 1952, and the data has none
- "Remove duplicates" removed nothing, while 662 rows repeat a song on another release. Each song is now counted once
- The README named a notebook file that didn't exist
- The release year was worked out twice, into two columns
- A four-second announcement credited to Spotify is no longer counted as a song

### Added

- A findings report with seven findings, every number worked out from the data
- Nine charts and three headline tiles, all drawn with [bezel-charts](https://pypi.org/project/bezel-charts/)
- `data/prepare.py`, a tidy data file and a record of the source and its licence in `data/sources.json`
- Tests, an automatic check on every pull request, Dependabot and a security policy
- Social preview image in `assets/social-preview.png`

### Changed

- New folder structure: `data/`, `findings/`, `notebooks/`, `charts/` and `tests/`
- The data now lives in the repo, so the notebook no longer downloads it from Kaggle each time
- README rewritten around the findings
- Notebook rewritten and moved to `notebooks/spotify_analysis.ipynb`
- The separate "Insights Report" file is replaced by `findings/README.md`

## November 2025

- First version: one notebook, the data, an insights report and a README

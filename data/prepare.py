"""Turn the Kaggle download into one tidy table of tracks.

The raw file is small, so it lives in data/raw/. To fetch it again, download "spotify_data clean.csv" from
https://www.kaggle.com/datasets/wardabilal/spotify-global-music-dataset-20092025, save it as
data/raw/spotify_data_clean.csv and run:

    python data/prepare.py

What this script changes, and why:

- Columns get shorter, plainer names, and each track gets its release year. Only the year is used: 667 tracks are dated
  1 January, which usually means the publisher only knew the year.
- Rows that aren't music are removed. There's one: a four-second announcement credited to Spotify itself.
- Genres are left out. 39% of tracks have none, so they can't be compared fairly.
- Many songs appear more than once, for example on an album and again as a single or on a compilation. Spotify scores
  each copy separately, so counting them all would count the same song twice. Each song is marked with a `song` key
  (its name and artist, ignoring case), and one copy per song, the most popular, is marked `counted`. Findings about
  songs use only the counted copies. Findings about copies use them all.
"""

import sys
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw" / "spotify_data_clean.csv"

COLUMNS = {
    "track_id": "track_id",
    "track_name": "track",
    "artist_name": "artist",
    "album_name": "album",
    "album_type": "release_type",
    "album_release_date": "release_date",
    "track_popularity": "popularity",
    "artist_popularity": "artist_popularity",
    "artist_followers": "artist_followers",
    "explicit": "explicit",
    "track_duration_min": "minutes",
    "track_number": "track_number",
    "album_total_tracks": "album_tracks",
}
NOT_MUSIC = {"Spotify"}  # Artist names used for announcements, not songs


def song_key(track: pd.Series, artist: pd.Series, track_id: pd.Series) -> pd.Series:
    """Name and artist, ignoring case and spaces at the ends. A track with no artist only matches itself."""
    clean = lambda s: s.str.lower().str.strip()  # noqa: E731
    return clean(track) + " | " + clean(artist).fillna("id:" + track_id)


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(columns=COLUMNS)[list(COLUMNS.values())].copy()
    d = d[~d["artist"].isin(NOT_MUSIC)]
    d["year"] = pd.to_datetime(d["release_date"], format="%Y-%m-%d").dt.year
    d["song"] = song_key(d["track"], d["artist"], d["track_id"])
    # The most popular copy of each song is the one counted. Ties go to the earliest release, then the track id.
    order = d.sort_values(["popularity", "release_date", "track_id"], ascending=[False, True, True])
    d["counted"] = d.index.isin(order.drop_duplicates("song").index)
    first = ["track_id", "song", "counted", "track", "artist", "album", "release_type", "release_date", "year"]
    return d[first + [c for c in d.columns if c not in first]].sort_values(["release_date", "track_id"]).reset_index(drop=True)


def main(raw_path: Path = RAW) -> None:
    tracks = tidy(pd.read_csv(raw_path))
    tracks.to_csv(DATA / "tracks.csv", index=False)
    print(f"{len(tracks):,} tracks, {tracks['counted'].sum():,} songs, {tracks['artist'].nunique():,} artists, "
          f"{tracks['year'].min()} to {tracks['year'].max()}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else RAW)

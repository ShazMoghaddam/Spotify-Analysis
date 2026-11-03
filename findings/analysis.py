"""The analysis behind every finding. Plain functions, no charts and no files written.

Most findings are about songs, so each song is counted once, using its most popular copy (see data/prepare.py).
Popularity is Spotify's own score from 0 to 100, read once when the data was collected in late 2025. It mostly
reflects how much a track is played around then, so it's a snapshot, not a lifetime total.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FIRST_YEAR = 2000  # Every year from here on has at least 50 songs, enough for a fair typical figure
SHORT = 3  # Minutes
PERIODS = {"2000 to 2009": (2000, 2009), "2010 to 2014": (2010, 2014), "2015 to 2019": (2015, 2019),
           "2020 to 2025": (2020, 2025)}


@lru_cache
def tracks() -> pd.DataFrame:
    """Every copy of every track, as tidied by data/prepare.py."""
    return pd.read_csv(DATA / "tracks.csv")


@lru_cache
def songs() -> pd.DataFrame:
    """One row per song: the most popular copy."""
    return tracks()[tracks()["counted"]].reset_index(drop=True)


# Finding 1: songs are getting shorter -------------------------------------------------------------------

def length_by_year() -> pd.DataFrame:
    s = songs()[songs()["year"] >= FIRST_YEAR]
    return s.groupby("year")["minutes"].agg(songs="size", typical="median")


def period(s: pd.DataFrame) -> pd.Series:
    labels = pd.Series(pd.NA, index=s.index, dtype="object")
    for name, (start, end) in PERIODS.items():
        labels[s["year"].between(start, end)] = name
    return labels


def length_by_period(rows: pd.DataFrame | None = None) -> pd.DataFrame:
    s = songs() if rows is None else rows
    groups = s.groupby(period(s))["minutes"]
    table = pd.DataFrame({"songs": groups.size(), "typical": groups.median(), "short": groups.apply(lambda m: (m < SHORT).mean())})
    return table.loc[list(PERIODS)]


def length_checks() -> pd.DataFrame:
    """The fall in typical length, checked on album tracks only and on popular songs only.

    If it held only for every song together, it could come from more short singles, or more obscure songs, being collected.
    """
    s = songs()
    groups = {
        "Every song": s,
        "Album tracks only": s[s["release_type"] == "album"],
        "Popular songs only (50 or more)": s[s["popularity"] >= 50],
    }
    first, last = list(PERIODS)[0], list(PERIODS)[-1]
    return pd.DataFrame({name: length_by_period(rows)["typical"][[first, last]] for name, rows in groups.items()}).T


# Finding 2: the same song gets different scores -----------------------------------------------------------

def copies() -> pd.DataFrame:
    """Songs that appear more than once, with the gap between their best and worst copy."""
    t = tracks()
    repeated = t[t["song"].duplicated(keep=False)]
    table = repeated.groupby("song")["popularity"].agg(copies="size", best="max", worst="min")
    table["gap"] = table["best"] - table["worst"]
    return table


def album_against(other: str) -> pd.DataFrame:
    """Songs found both on an album and on another kind of release, with each one's best score."""
    t = tracks()
    best = t.pivot_table(index="song", columns="release_type", values="popularity", aggfunc="max")
    return best.dropna(subset=["album", other])[["album", other]]


def by_release_type() -> pd.Series:
    return songs().groupby("release_type")["popularity"].median().reindex(["album", "single", "compilation"])


def example(song: str = "mood (feat. iann dior) | 24kgoldn") -> pd.DataFrame:
    return tracks().loc[tracks()["song"] == song, ["track", "artist", "album", "release_type", "popularity"]]


# Finding 3: a score of zero doesn't mean nobody listens -------------------------------------------------------

BANDS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 101]


def popularity_bands() -> pd.Series:
    labels = [f"{low} to {high - 1}" for low, high in zip(BANDS[:-1], BANDS[1:])]
    labels[-1] = "90 to 100"
    return pd.cut(songs()["popularity"], BANDS, right=False, labels=labels).value_counts(sort=False)


def zeros() -> dict:
    s = songs()
    zero = s[s["popularity"] == 0]
    return {
        "zero": len(zero), "share": len(zero) / len(s), "under_10": (s["popularity"] < 10).mean(),
        "big_artists": int((zero["artist_popularity"] >= 70).sum()),
        "artist_typical": zero["artist_popularity"].median(),
        "examples": zero.nlargest(3, "artist_popularity")[["track", "artist", "artist_popularity"]],
    }


# Finding 4: big artists help, but don't decide -------------------------------------------------------------

ARTIST_BANDS = {"Under 50": (0, 49), "50s": (50, 59), "60s": (60, 69), "70s": (70, 79), "80s": (80, 89), "90 and up": (90, 100)}


def by_artist() -> pd.DataFrame:
    s = songs()
    rows = {}
    for name, (low, high) in ARTIST_BANDS.items():
        p = s.loc[s["artist_popularity"].between(low, high), "popularity"]
        rows[name] = {"songs": len(p), "typical": p.median(), "low": p.quantile(0.25), "high": p.quantile(0.75)}
    return pd.DataFrame(rows).T


def artist_link() -> dict:
    s = songs()
    r = s["artist_popularity"].corr(s["popularity"])
    top = s[s["artist_popularity"] >= 90]
    return {"r": r, "explained": r ** 2, "top_under_50": (top["popularity"] < 50).mean()}


# Finding 5: length barely matters, except for very short tracks ----------------------------------------------

LENGTH_BANDS = {"Under 2": (0, 2), "2 to 2.5": (2, 2.5), "2.5 to 3": (2.5, 3), "3 to 3.5": (3, 3.5), "3.5 to 4": (3.5, 4),
                "4 to 5": (4, 5), "5 and over": (5, 999)}


def by_length() -> pd.DataFrame:
    s = songs()
    rows = {}
    for name, (low, high) in LENGTH_BANDS.items():
        p = s.loc[(s["minutes"] >= low) & (s["minutes"] < high), "popularity"]
        rows[name] = {"songs": len(p), "typical": p.median()}
    return pd.DataFrame(rows).T


def length_link() -> dict:
    s = songs()
    two_plus = s[s["minutes"] >= 2]
    return {"r": s["minutes"].corr(s["popularity"]), "r_two_plus": two_plus["minutes"].corr(two_plus["popularity"])}


# Finding 6: more songs are explicit, and they score higher -----------------------------------------------------

DECADES = {"1960s": (1950, 1969), "1970s": (1970, 1979), "1980s": (1980, 1989), "1990s": (1990, 1999),
           "2000s": (2000, 2009), "2010s": (2010, 2019), "2020s": (2020, 2029)}


def explicit_by_decade() -> pd.DataFrame:
    """The 1960s include the seven songs from the 1950s, too few to stand alone."""
    s = songs()
    rows = {}
    for name, (start, end) in DECADES.items():
        e = s.loc[s["year"].between(start, end), "explicit"]
        rows[name] = {"songs": len(e), "share": e.mean()}
    return pd.DataFrame(rows).T


def explicit_scores() -> pd.DataFrame:
    """Typical popularity of explicit and clean songs, within each period, so the trend over time can't explain it."""
    s = songs()
    s = s[s["year"] >= FIRST_YEAR]
    table = s.groupby([period(s), "explicit"])["popularity"].median().unstack()
    return table.loc[list(PERIODS)].rename(columns={False: "clean", True: "explicit"})


HIP_HOP = "hip hop|rap|trap|drill"


def explicit_by_genre() -> pd.DataFrame:
    """Typical popularity of explicit and clean tracks, inside and outside hip-hop and rap.

    Genres are missing for 39% of tracks, so this uses only the tracks that have one, straight from the raw file.
    It's a check on finding 6, not a finding of its own.
    """
    raw = pd.read_csv(DATA / "raw" / "spotify_data_clean.csv").dropna(subset=["artist_genres"])
    hip_hop = raw["artist_genres"].str.contains(HIP_HOP, case=False).map({True: "Hip-hop and rap", False: "Everything else"})
    table = raw.groupby([hip_hop, "explicit"])["track_popularity"].median().unstack()
    table = table.rename(columns={False: "clean", True: "explicit"})
    table["explicit_share"] = raw.groupby(hip_hop)["explicit"].mean()
    table.attrs["tracks"] = len(raw)
    table.attrs["hip_hop_share_of_explicit"] = (hip_hop[raw["explicit"]] == "Hip-hop and rap").mean()
    table.attrs["hip_hop_share_of_clean"] = (hip_hop[~raw["explicit"]] == "Hip-hop and rap").mean()
    return table


# What the first version got wrong ------------------------------------------------------------------------------

def first_version() -> dict:
    """The first version ranked artists by rows in the file and charted rows per year. Both measure the sample."""
    t = tracks()
    rows = t["artist"].value_counts()
    nirvana = t[t["artist"] == "Nirvana"]
    deluxe = "Nevermind (Super Deluxe Edition)"
    year_1991 = t[t["year"] == 1991]
    swift = t[t["artist"] == "Taylor Swift"]
    return {
        "top": rows.head(10), "nirvana_rows": len(nirvana), "nirvana_deluxe": int((nirvana["album"] == deluxe).sum()),
        "rows_1991": len(year_1991), "deluxe_1991": int((year_1991["album"] == deluxe).sum()),
        "swift_rows": len(swift), "swift_albums": swift["album"].nunique(),
        "swift_biggest": swift["album"].value_counts().head(1),
    }


def rows_by_year() -> pd.Series:
    """Tracks in the file for every year, including the few years with none."""
    counts = tracks().groupby("year").size()
    return counts.reindex(range(counts.index.min(), counts.index.max() + 1), fill_value=0)


# Data quality, for the report and the changelog ------------------------------------------------------------------

def data_notes() -> dict:
    raw = pd.read_csv(DATA / "raw" / "spotify_data_clean.csv")
    t = tracks()
    s = songs()
    return {
        "raw_rows": len(raw), "rows": len(t), "songs": len(s), "artists": t["artist"].nunique(),
        "first_year": int(t["year"].min()), "last_year": int(t["year"].max()), "latest": t["release_date"].max(),
        "repeats": len(t) - len(s), "no_genre": raw["artist_genres"].isna().mean(),
        "new_year": int(t["release_date"].str.endswith("-01-01").sum()), "no_artist": int(t["artist"].isna().sum()),
        "not_music": len(raw) - len(t), "exact_duplicates": int(raw.duplicated().sum()),
        "since_2000": (s["year"] >= FIRST_YEAR).mean(),
    }

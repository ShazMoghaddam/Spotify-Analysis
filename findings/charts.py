"""Every chart in the project, drawn with bezel-charts (https://pypi.org/project/bezel-charts/).

Each function returns a chart, which shows up in a notebook and saves as an SVG.

The look is this project's own: dark tiles with squarer corners, and colours from the Okabe-Ito set, which stay
distinct for people with every common kind of colour blindness. Sky blue is the main colour and orange the second.
"""

from __future__ import annotations

import pandas as pd

import bezel_charts as bc

try:
    from . import analysis as an
except ImportError:
    import analysis as an

SKY, ORANGE, PINK, YELLOW = "#56B4E9", "#E69F00", "#CC79A7", "#F0E442"
STYLE = {"theme": "dark", "corners": 8}
WIDE = {**STYLE, "width": 720}
TILE = {**STYLE, "width": 236}


def years(series: pd.Series) -> pd.Series:
    series = series.copy()
    series.index = series.index.astype(str)
    return series


def song_length():
    typical = years(an.length_by_year()["typical"]).round(2)
    return bc.line(
        typical, heading="Typical song length by release year, in minutes", stat="none", height=240, straight=True,
        zero=True, decimals=1, suffix=" min", color=SKY, notes={"2024": "2.9 min"}, **WIDE,
    )


def short_songs():
    share = (an.length_by_period()["short"] * 100).round(0)
    return bc.bars(
        share, heading="Share of songs under 3 minutes, by release year", stat="none", show_values=True, suffix="%",
        decimals=0, height=220, highlight="none", color=ORANGE, **WIDE,
    )


def same_song():
    rows = {}
    for other, name in (("compilation", "compilation"), ("single", "single")):
        pairs = an.album_against(other)
        rows[f"Album and {name} ({len(pairs)} songs)"] = {"On the album": pairs["album"].median(),
                                                         "On the other release": pairs[other].median()}
    table = pd.DataFrame(rows).T.round(0)
    return bc.bars(
        table, heading="Typical score for the same song, on each of its releases", stat="none", show_values=True,
        decimals=0, height=230, color=[SKY, ORANGE], **WIDE,
    )


def scores():
    bands = an.popularity_bands()
    colours = [ORANGE] + [SKY] * (len(bands) - 1)
    return bc.bars(
        bands, heading="Songs by popularity score, out of 100", stat="none", show_values=True, decimals=0, height=230,
        color=colours, **WIDE,
    )


def by_artist():
    typical = an.by_artist()["typical"].round(0)
    return bc.bars(
        typical, heading="Typical song score, by how popular its artist is", stat="none", show_values=True, decimals=0,
        height=220, highlight="none", color=SKY, **WIDE,
    )


def by_length():
    typical = an.by_length()["typical"].round(0)
    colours = [ORANGE] + [SKY] * (len(typical) - 1)
    return bc.bars(
        typical, heading="Typical song score, by length in minutes", stat="none", show_values=True, decimals=0,
        height=220, color=colours, **WIDE,
    )


def explicit():
    share = (an.explicit_by_decade()["share"] * 100).round(0)
    return bc.bars(
        share, heading="Share of songs marked explicit, by decade of release", stat="none", show_values=True,
        suffix="%", decimals=0, height=220, highlight="none", color=PINK, **WIDE,
    )


def explicit_scores():
    table = an.explicit_scores().round(0)
    table.columns = ["Clean", "Explicit"]
    return bc.bars(
        table, heading="Typical score of clean and explicit songs, by release year", stat="none", show_values=True,
        decimals=0, height=230, color=[SKY, PINK], **WIDE,
    )


def rows_by_year():
    rows = years(an.rows_by_year().loc[1960:])
    return bc.line(
        rows, heading="Tracks in the file, by release year, 1960 to 2025", stat="none", height=220, straight=True, zero=True,
        decimals=0, color=SKY, notes={"1991": "One deluxe album"}, **WIDE,
    )


# Headline tiles ------------------------------------------------------------------------------------

def tile_length():
    return bc.spark(
        years(an.length_by_year()["typical"]).round(2), heading="Typical song length, 2025", suffix=" min", decimals=1,
        delta="none", straight=True, height=86, color=SKY, **TILE,
    )


def tile_short():
    share = an.length_by_period()["short"].iloc[-1]
    return bc.gauge(
        round(share * 100), label="under 3 minutes", heading="Songs since 2020", suffix="%", color=ORANGE, **TILE,
    )


def tile_copies():
    pairs = an.album_against("compilation").median().round(0)
    pairs.index = ["Album", "Compilation"]
    return bc.bars(
        pairs, heading="Same song, two scores", stat="none", show_values=True, decimals=0, height=128,
        color=[SKY, ORANGE], **TILE,
    )


ALL = {
    "song-length": song_length,
    "short-songs": short_songs,
    "same-song": same_song,
    "scores": scores,
    "by-artist": by_artist,
    "by-length": by_length,
    "explicit": explicit,
    "explicit-scores": explicit_scores,
    "rows-by-year": rows_by_year,
    "tile-length": tile_length,
    "tile-short": tile_short,
    "tile-copies": tile_copies,
}

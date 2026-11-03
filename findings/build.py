"""Draw every chart and write the findings report.

Run from the repository root:

    python findings/build.py

Charts go into charts/ as SVG files. The report is written to findings/README.md, and the key findings in the
main README are rewritten between their marker comments. Every number is worked out from the data. Nothing in
them is typed in by hand.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "findings"))

import analysis as an  # noqa: E402
import charts  # noqa: E402

CHARTS = ROOT / "charts"
REPORT = ROOT / "findings" / "README.md"
README = ROOT / "README.md"


def mmss(minutes: float) -> str:
    """3.735 becomes "3 minutes 44 seconds"."""
    whole, seconds = divmod(round(minutes * 60), 60)
    return f"{whole} minutes {seconds} seconds"


def facts() -> dict:
    """Every number the writing uses, in one place."""
    notes = an.data_notes()
    periods = an.length_by_period()
    first, last = periods.index[0], periods.index[-1]
    checks = an.length_checks()
    by_year = an.length_by_year()["typical"]
    copies = an.copies()
    compilation, single = an.album_against("compilation"), an.album_against("single")
    types = an.by_release_type()
    mood = an.example().set_index("release_type")["popularity"]
    zeros = an.zeros()
    bands = an.popularity_bands()
    artist = an.by_artist()
    link = an.artist_link()
    length = an.by_length()
    length_link = an.length_link()
    explicit = an.explicit_by_decade()["share"]
    explicit_scores = an.explicit_scores()
    old = an.first_version()
    genre = an.explicit_by_genre()
    examples = zeros["examples"]
    return {
        **notes,
        "first": first, "last": last,
        "len_first": mmss(periods.loc[first, "typical"]), "len_last": mmss(periods.loc[last, "typical"]),
        "len_first_n": int(periods.loc[first, "songs"]), "len_last_n": int(periods.loc[last, "songs"]),
        "short_first": periods.loc[first, "short"], "short_last": periods.loc[last, "short"],
        "short_mid": periods.loc["2010 to 2014", "short"],
        "low_year": int(by_year.idxmin()), "low_len": mmss(by_year.min()),
        "album_first": mmss(checks.loc["Album tracks only", first]), "album_last": mmss(checks.loc["Album tracks only", last]),
        "pop_first": mmss(checks.loc["Popular songs only (50 or more)", first]),
        "pop_last": mmss(checks.loc["Popular songs only (50 or more)", last]),
        "fall": 1 - periods.loc[last, "typical"] / periods.loc[first, "typical"],
        "repeated": len(copies), "repeated_rows": int(copies["copies"].sum()), "gap_typical": copies["gap"].median(),
        "gap_20": (copies["gap"] >= 20).mean(),
        "comp_n": len(compilation), "comp_album": compilation["album"].median(), "comp_other": compilation["compilation"].median(),
        "comp_wins": (compilation["album"] > compilation["compilation"]).mean(),
        "single_n": len(single), "single_album": single["album"].median(), "single_other": single["single"].median(),
        "single_wins": (single["album"] > single["single"]).mean(),
        "type_album": types["album"], "type_single": types["single"], "type_comp": types["compilation"],
        "mood_album": mood["album"], "mood_single": mood["single"],
        "zero": zeros["zero"], "zero_share": zeros["share"], "under_10": zeros["under_10"],
        "zero_big": zeros["big_artists"], "zero_artist": zeros["artist_typical"],
        "ex1": examples.iloc[0]["track"], "ex1_artist": examples.iloc[0]["artist"],
        "ex3": examples.iloc[2]["track"], "ex3_artist": examples.iloc[2]["artist"],
        "peak_band": bands.idxmax(), "band_60_79": (bands["60 to 69"] + bands["70 to 79"]) / bands.sum(),
        "a_low": artist.loc["Under 50", "typical"], "a_high": artist.loc["90 and up", "typical"],
        "a_low_n": int(artist.loc["Under 50", "songs"]), "a_high_n": int(artist.loc["90 and up", "songs"]),
        "a_r": link["r"], "a_explained": link["explained"], "a_top_under_50": link["top_under_50"],
        "a_high_low": artist.loc["90 and up", "low"], "a_high_high": artist.loc["90 and up", "high"],
        "l_r": length_link["r"], "l_r2": length_link["r_two_plus"],
        "l_short": length.loc["Under 2", "typical"], "l_short_n": int(length.loc["Under 2", "songs"]),
        "l_best": length["typical"].idxmax(), "l_best_v": length["typical"].max(),
        "e_first": explicit.iloc[0], "e_1990": explicit["1990s"], "e_2000": explicit["2000s"], "e_last": explicit.iloc[-1],
        "es_first_clean": explicit_scores.iloc[0]["clean"], "es_first_explicit": explicit_scores.iloc[0]["explicit"],
        "es_last_clean": explicit_scores.iloc[-1]["clean"], "es_last_explicit": explicit_scores.iloc[-1]["explicit"],
        "g_tracks": genre.attrs["tracks"], "g_hip_explicit": genre.attrs["hip_hop_share_of_explicit"],
        "g_hip_clean": genre.attrs["hip_hop_share_of_clean"],
        "g_hh_e": genre.loc["Hip-hop and rap", "explicit"], "g_hh_c": genre.loc["Hip-hop and rap", "clean"],
        "g_other_e": genre.loc["Everything else", "explicit"], "g_other_c": genre.loc["Everything else", "clean"],
        "nirvana_rows": old["nirvana_rows"], "nirvana_deluxe": old["nirvana_deluxe"], "nirvana_rank": list(old["top"].index).index("Nirvana") + 1,
        "rows_1991": old["rows_1991"], "deluxe_1991": old["deluxe_1991"],
        "swift_rows": old["swift_rows"], "swift_albums": old["swift_albums"],
        "swift_biggest": old["swift_biggest"].index[0], "swift_biggest_n": int(old["swift_biggest"].iloc[0]),
    }


def key_findings(f: dict) -> str:
    return f"""### Songs are getting shorter

The typical song released from {f['first']} lasts **{f['len_first']}**. From {f['last']} it's **{f['len_last']}**. Nearly half of
recent songs ({f['short_last']:.0%}) are under 3 minutes, against {f['short_first']:.0%} in the 2000s.

![Typical song length by release year](charts/song-length.svg)

### The same song can score {f['comp_album']:.0f} or {f['comp_other']:.0f}

Spotify scores every copy of a song separately. For {f['comp_n']} songs that are on both an album and a compilation, the
album copy typically scores **{f['comp_album']:.0f}** out of 100 and the compilation copy **{f['comp_other']:.0f}**.

![Typical score for the same song on each of its releases](charts/same-song.svg)

### A score of zero doesn't mean nobody listens

{f['zero']} songs score exactly 0, and {f['zero_big']} of them are by artists who score 70 or more, such as {f['ex3_artist']}'s "{f['ex3']}".
The first version called the scores "normal-like". They aren't.

![Songs by popularity score](charts/scores.svg)

### Big artists help, but they don't decide

Songs by the least popular artists typically score **{f['a_low']:.0f}**, and songs by the most popular **{f['a_high']:.0f}**. But how
popular the artist is explains only about **{f['a_explained']:.0%}** of the differences between songs.

![Typical song score by how popular its artist is](charts/by-artist.svg)"""


def report(f: dict) -> str:
    return f"""# Findings

What {f['songs']:,} songs on Spotify can and can't tell you. This page is written by [`build.py`](build.py), so every number comes
straight from the data.

The data is a sample of {f['rows']:,} tracks by {f['artists']:,} artists, released from {f['first_year']} to {f['last_year']}. Many songs appear more than once,
for example on an album and again on a compilation, so most findings count each song once, using its most popular
copy. That leaves {f['songs']:,} songs.

**Popularity** is Spotify's own score, from 0 to 100. Spotify says it's based mostly on how many times a track has been
played and how recent those plays are. Each score here was read once, in late 2025, so it's a snapshot of what people
were listening to then, not a lifetime total.

## 1. Songs are getting shorter

The typical song released from {f['first']} lasts {f['len_first']} ({f['len_first_n']} songs). From {f['last']} it's
{f['len_last']} ({f['len_last_n']:,} songs), {f['fall']:.0%} shorter. The shortest year is {f['low_year']}, at {f['low_len']}.

![Typical song length by release year, in minutes](../charts/song-length.svg)

The change is sharpest at the short end. {f['short_first']:.0%} of songs from the 2000s are under 3 minutes, and {f['short_mid']:.0%} from 2010 to
2014. From {f['last']} it's **{f['short_last']:.0%}**, nearly half.

![Share of songs under 3 minutes](../charts/short-songs.svg)

Two checks make sure this isn't a quirk of which songs were collected. Counting only album tracks, the typical length
still falls, from {f['album_first']} to {f['album_last']}. Counting only songs that score 50 or more, it falls from
{f['pop_first']} to {f['pop_last']}.

The data doesn't say why. Two reasons often given are that streaming counts a play the same however long the song is,
and that short songs suit short videos. Neither is measured here.

## 2. The same song can get very different scores

Spotify gives every copy of a song its own score. {f['repeated']} songs appear more than once in the data, {f['repeated_rows']:,} copies in
all, and for {f['gap_20']:.0%} of them the best and worst copy are {f['gap_typical']:.0f} or more points apart.

For example, 24kGoldn's "Mood" scores {f['mood_album']:.0f} on the album and {f['mood_single']:.0f} as a single. Plays tend to gather on one copy, and
the others are left with few.

![Typical score for the same song on each of its releases](../charts/same-song.svg)

The album copy usually wins. For the {f['comp_n']} songs on both an album and a compilation, the album copy scores
higher {f['comp_wins']:.0%} of the time, typically {f['comp_album']:.0f} against {f['comp_other']:.0f}. For the {f['single_n']} songs on both an album and a single, it scores
higher {f['single_wins']:.0%} of the time, {f['single_album']:.0f} against {f['single_other']:.1f}.

So a song's score depends on which copy you look at. Counting each song once, typical scores are {f['type_album']:.0f} for album
tracks, {f['type_single']:.0f} for singles and {f['type_comp']:.0f} for compilation tracks.

## 3. A score of zero doesn't mean nobody listens

{f['zero']} songs ({f['zero_share']:.1%}) score exactly 0. That's not because nobody has heard them. {f['zero_big']} are by artists who
score 70 or more, and the typical zero-scoring song is by an artist who scores {f['zero_artist']:.0f}. They include {f['ex1_artist']}'s
"{f['ex1']}" and {f['ex3_artist']}'s "{f['ex3']}". The likely reason is the one in finding 2: plays are counted on another copy that
isn't in this sample.

![Songs by popularity score, out of 100](../charts/scores.svg)

The first version said popularity follows "a normal-like distribution". It doesn't. The most common scores are 60 to 79
({f['band_60_79']:.0%} of songs), very few songs score 90 or more, and {f['under_10']:.0%} score under 10, more than score 10 to 19.

## 4. Big artists help, but they don't decide

Every artist has a popularity score too. Songs by artists who score under 50 ({f['a_low_n']:,} songs) typically score {f['a_low']:.0f}.
Songs by artists who score 90 or more ({f['a_high_n']:,} songs) typically score {f['a_high']:.0f}.

![Typical song score by how popular its artist is](../charts/by-artist.svg)

The link is real but loose. The correlation is {f['a_r']:.2f} (1 would be a perfect straight line), which means the artist's
score explains about {f['a_explained']:.0%} of the differences between songs. Even for the biggest artists, the middle half of their
songs score anywhere from {f['a_high_low']:.0f} to {f['a_high_high']:.0f}, and {f['a_top_under_50']:.0%} score under 50.

## 5. Length barely matters, except for very short tracks

Across all songs, the correlation between length and score is only {f['l_r']:.2f}. Leaving out tracks under 2 minutes, it's
{f['l_r2']:.2f}, which is no link at all. The first version was right about this.

![Typical song score by length](../charts/by-length.svg)

The exception is the shortest tracks. The {f['l_short_n']} tracks under 2 minutes typically score {f['l_short']:.0f}, against {f['l_best_v']:.0f} for songs of
{f['l_best']} minutes. Many are intros, interludes and voice memos rather than full songs.

## 6. More songs are explicit, and explicit songs score higher

None of the songs from the 1950s and 1960s is marked explicit. {f['e_1990']:.0%} from the 1990s are, {f['e_2000']:.0%} from the 2000s, and
**{f['e_last']:.0%}** from the 2020s.

![Share of songs marked explicit, by decade](../charts/explicit.svg)

Explicit songs also score higher in every period: {f['es_first_explicit']:.0f} against {f['es_first_clean']:.0f} for clean songs from {f['first']}, and
{f['es_last_explicit']:.0f} against {f['es_last_clean']:.0f} from {f['last']}. Comparing within each period means this isn't only because explicit songs
are newer.

![Typical score of clean and explicit songs](../charts/explicit-scores.svg)

Is the label just standing in for hip-hop and rap? Among the {f['g_tracks']:,} tracks that have a genre, {f['g_hip_explicit']:.0%} of explicit
tracks are hip-hop or rap, against {f['g_hip_clean']:.0%} of clean ones. But explicit tracks score higher on both sides: {f['g_hh_e']:.0f}
against {f['g_hh_c']:.0f} within hip-hop and rap, and {f['g_other_e']:.0f} against {f['g_other_c']:.0f} for everything else. So genre doesn't explain it.

It's still a link, not a cause. The data can't say whether explicit lyrics draw listeners or something else does.

## 7. What the first version got wrong

- **Its top 10 artists counted rows, not popularity.** Nirvana came {f['nirvana_rank']}th with {f['nirvana_rows']} tracks, but {f['nirvana_deluxe']} of them are from one
  album, the *Nevermind (Super Deluxe Edition)*. Taylor Swift came first with {f['swift_rows']} tracks from {f['swift_albums']} different albums,
  including {f['swift_biggest_n']} from the "{f['swift_biggest']}".
- **Its "music production" chart counted the sample, not the industry.** The number of tracks per year mostly rises
  because the sample favours recent music. The spike in 1991 is that same deluxe album: {f['deluxe_1991']} of the year's {f['rows_1991']} tracks.

![Tracks in the file by release year](../charts/rows-by-year.svg)

- **Its scatter plot had its axes swapped.** The chart labelled "Artist Popularity" along the bottom was really showing
  track popularity, and the other way round.
- **It called popularity "normal-like".** See finding 3.
- **Its title said 2009 to 2025, and it promised audio features.** The songs go back to {f['first_year']}, and the data has no
  audio features such as tempo or energy.

## What this data can't tell you

- **Whether music as a whole changed.** This is a sample of songs on Spotify in 2025, not every song ever released. Old
  songs are only here if they're still played, so earlier years are mostly hits. The checks in finding 1 help, but
  can't rule this out completely.
- **How popular a song has been over time.** Each score was read once, in late 2025, and Spotify weighs recent plays
  most. A song that was huge in 2005 can score lower than an average song from last month.
- **Why anything happened.** The data shows patterns, not causes.
- **Much about genre.** {f['no_genre']:.0%} of tracks have no genre, so genres are only used for one check in finding 6.

## About the data

The data was collected from Spotify's public API and published on Kaggle as the "Spotify Global Music Dataset
(2009–2025)", under a public domain licence (CC0). A few things needed fixing before it could be used:

- **{f['repeats']} rows repeat a song** already in the data, on another release. Each song is counted once in most findings,
  using its most popular copy. See [`data/prepare.py`](../data/prepare.py).
- **{f['new_year']} tracks are dated 1 January**, which usually means only the year was known. Only release years are used.
- **One row isn't music:** a four-second announcement credited to Spotify. It's removed.
- **{f['no_artist']} tracks have no artist name.** They're kept, and each one only matches itself.
- **{f['since_2000']:.0%} of songs were released in {an.FIRST_YEAR} or later.** Years before that have too few songs for a fair typical
  figure, so findings over time start in {an.FIRST_YEAR}.

## How it was worked out

1. [`data/prepare.py`](../data/prepare.py) tidies the download, removes the announcement and marks one copy of each song to count.
2. [`analysis.py`](analysis.py) holds every calculation as a small, tested function.
3. [`charts.py`](charts.py) draws each chart with [bezel-charts](https://pypi.org/project/bezel-charts/).
4. [`notebooks/spotify_analysis.ipynb`](../notebooks/spotify_analysis.ipynb) walks through the same steps with the working shown.
"""


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(\n<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"Marker {name} not found")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def main() -> None:
    # bezel-charts gives each gradient a random id so charts can share a page. A fixed seed keeps the
    # files identical between runs, so a rebuild only shows up in git when something really changed.
    random.seed(2026)
    CHARTS.mkdir(exist_ok=True)
    for name, draw in charts.ALL.items():
        draw().save(CHARTS / f"{name}.svg")
    f = facts()
    REPORT.write_text(report(f), encoding="utf-8")
    README.write_text(replace_block(README.read_text(encoding="utf-8"), "key-findings", key_findings(f)), encoding="utf-8")
    print(f"Wrote {len(charts.ALL)} charts, {REPORT.relative_to(ROOT)} and the README findings")


if __name__ == "__main__":
    main()

"""Checks that the data is sound and the findings hold up. Run from the repository root with `pytest`."""

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "findings"), str(ROOT / "data")]

import analysis as an  # noqa: E402
import charts  # noqa: E402
import prepare  # noqa: E402


def raw(*rows) -> pd.DataFrame:
    """A tiny download. Each row is (track id, track, artist, release type, popularity)."""
    frame = pd.DataFrame(rows, columns=["track_id", "track_name", "artist_name", "album_type", "track_popularity"])
    frame["album_name"] = "Album"
    frame["album_release_date"] = "2020-05-01"
    frame["artist_popularity"] = 50
    frame["artist_followers"] = 1000
    frame["explicit"] = False
    frame["track_duration_min"] = 3.0
    frame["track_number"] = 1
    frame["album_total_tracks"] = 10
    frame["artist_genres"] = None
    return frame


# Preparing the data -------------------------------------------------------------------------------------

def test_each_song_is_counted_once_using_its_most_popular_copy():
    d = prepare.tidy(raw(("a", "Mood", "24kGoldn", "single", 6), ("b", "mood ", "24KGOLDN", "album", 77),
                         ("c", "Other", "24kGoldn", "album", 40)))
    assert d["song"].nunique() == 2
    assert d.loc[d["counted"], "track_id"].tolist() == ["b", "c"]


def test_tracks_with_no_artist_only_match_themselves():
    d = prepare.tidy(raw(("a", "Radio", None, "album", 10), ("b", "Radio", None, "album", 20)))
    assert d["counted"].all()


def test_announcements_are_removed():
    d = prepare.tidy(raw(("a", "Up next: A few songs", "Spotify", "album", 0), ("b", "Song", "Band", "album", 50)))
    assert d["track_id"].tolist() == ["b"]


def test_release_year_comes_from_the_date():
    assert prepare.tidy(raw(("a", "Song", "Band", "album", 50)))["year"].tolist() == [2020]


# The data in the repo ---------------------------------------------------------------------------------------

def test_raw_download_is_complete():
    d = pd.read_csv(an.DATA / "raw" / "spotify_data_clean.csv")
    assert d.shape == (8582, 15)
    assert d["track_id"].is_unique


def test_tidy_file_matches_prepare():
    fresh = prepare.tidy(pd.read_csv(an.DATA / "raw" / "spotify_data_clean.csv"))
    saved = pd.read_csv(an.DATA / "tracks.csv")
    pd.testing.assert_frame_equal(fresh, saved, check_dtype=False)


def test_one_counted_copy_per_song():
    t = an.tracks()
    assert t.groupby("song")["counted"].sum().eq(1).all()
    assert len(an.songs()) == t["song"].nunique()


def test_scores_and_lengths_are_in_range():
    t = an.tracks()
    assert t["popularity"].between(0, 100).all() and t["artist_popularity"].between(0, 100).all()
    assert t["minutes"].between(0.1, 15).all(), "the announcement was the only track under 6 seconds"


# The findings ---------------------------------------------------------------------------------------------------

def test_songs_got_shorter():
    periods = an.length_by_period()
    assert periods["typical"].iloc[0] - periods["typical"].iloc[-1] > 0.5
    assert periods["short"].iloc[-1] > 2 * periods["short"].iloc[0]


def test_songs_got_shorter_on_albums_and_among_popular_songs_too():
    checks = an.length_checks()
    assert (checks.iloc[:, 0] - checks.iloc[:, 1] > 0.5).all()


def test_the_same_song_scores_differently_on_each_release():
    assert an.copies()["gap"].median() >= 15
    pairs = an.album_against("compilation")
    assert (pairs["album"] > pairs["compilation"]).mean() > 0.8
    assert an.example().set_index("release_type")["popularity"].to_dict() == {"single": 6, "album": 77}


def test_zero_scores_include_big_artists():
    zeros = an.zeros()
    assert zeros["zero"] > 400 and zeros["big_artists"] >= 50


def test_scores_are_not_a_bell_curve():
    """A bell curve would have fewer songs at 0 to 9 than at 10 to 19."""
    bands = an.popularity_bands()
    assert bands["0 to 9"] > 3 * bands["10 to 19"]


def test_artists_explain_some_but_not_most_of_a_songs_score():
    link = an.artist_link()
    assert 0.2 < link["explained"] < 0.35
    typical = an.by_artist()["typical"]
    assert typical.iloc[-1] > typical.iloc[0] + 30


def test_length_barely_matters_beyond_two_minutes():
    assert abs(an.length_link()["r_two_plus"]) < 0.1
    assert an.by_length()["typical"].idxmin() == "Under 2"


def test_explicit_songs_grew_and_score_higher():
    share = an.explicit_by_decade()["share"]
    assert share["1960s"] == 0 and share["2020s"] > 0.25
    scores = an.explicit_scores()
    assert (scores["explicit"] > scores["clean"]).all()
    genre = an.explicit_by_genre()
    assert (genre["explicit"] > genre["clean"]).all(), "explicit should score higher inside and outside hip-hop"


def test_the_first_versions_top_artists_and_1991_spike_came_from_one_album():
    old = an.first_version()
    assert list(old["top"].index[:2]) == ["Taylor Swift", "The Weeknd"]
    assert old["deluxe_1991"] / old["rows_1991"] > 0.7


# The outputs ---------------------------------------------------------------------------------------------------

def test_every_chart_is_built():
    for name in charts.ALL:
        assert (ROOT / "charts" / f"{name}.svg").exists(), name


@pytest.mark.parametrize("page", ["README.md", "findings/README.md"])
def test_pages_link_to_real_files_and_have_no_gaps(page):
    path = ROOT / page
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\{f\[|\bnan\b|\bNone\b(?! of)", text)
    for link in re.findall(r"\]\(((?:\.\./)?[\w/.-]+\.(?:svg|py|md|ipynb|json))\)", text):
        assert (path.parent / link).resolve().exists(), link


def test_readme_ends_with_the_signature():
    text = (ROOT / "README.md").read_text(encoding="utf-8").rstrip()
    assert text.endswith("---\n\nCreated by **Shaz Moghaddam** · London\n"
                         "[Website](https://shazmoghaddam.github.io) · [LinkedIn](https://www.linkedin.com/in/shazmoghaddam)")

import pytest

from nuscroll import disqus
from nuscroll.disqus import DisqusError, fetch_reviews, html_to_text


def test_html_to_text_basic():
    assert html_to_text("<p>Great mod</p>") == "Great mod"


def test_html_to_text_breaks_and_entities():
    out = html_to_text("line one<br>line two &amp; more")
    assert out == "line one\nline two & more"


def test_fetch_reviews_paginates_and_maps():
    pages = {
        "page1": {
            "code": 0,
            "cursor": {"hasNext": True, "next": "CURSOR2"},
            "response": [
                {"message": "<p>first</p>", "author": {"name": "A"},
                 "createdAt": "2024-01-01T00:00:00", "likes": 1, "isDeleted": False},
            ],
        },
        "page2": {
            "code": 0,
            "cursor": {"hasNext": False, "next": None},
            "response": [
                {"message": "<p>second</p>", "author": {"name": "B"},
                 "createdAt": "2024-02-01T00:00:00", "likes": 0, "isDeleted": False},
                {"message": "deleted", "author": {"name": "C"},
                 "createdAt": "2024-03-01T00:00:00", "likes": 0, "isDeleted": True},
            ],
        },
    }

    def fake_fetch(url):
        return pages["page2"] if "CURSOR2" in url else pages["page1"]

    reviews = fetch_reviews("CS2100", "KEY", fetch_json=fake_fetch)
    assert [r.author for r in reviews] == ["A", "B"]   # deleted C skipped
    assert reviews[0].message == "first"
    assert reviews[1].likes == 0


def test_fetch_reviews_raises_on_api_error():
    def fake_fetch(url):
        return {"code": 5, "response": "Invalid API key"}

    with pytest.raises(DisqusError) as exc:
        fetch_reviews("CS2100", "BAD", fetch_json=fake_fetch)
    assert exc.value.code == 5


def test_fetch_reviews_handles_null_author():
    def fake_fetch(url):
        return {
            "code": 0,
            "cursor": {"hasNext": False, "next": None},
            "response": [
                {"message": "<p>hi</p>", "author": None,
                 "createdAt": "2024-01-01T00:00:00", "likes": 0, "isDeleted": False},
            ],
        }

    reviews = fetch_reviews("CS2100", "KEY", fetch_json=fake_fetch)
    assert reviews[0].author == "anonymous"

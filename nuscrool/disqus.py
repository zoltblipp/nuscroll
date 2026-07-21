"""Disqus API client for NUSMods course review threads."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser

from nuscrool.models import Review

_API = "https://disqus.com/api/3.0/threads/listPosts.json"
_BREAK_TAGS = {"br", "p", "div"}


class DisqusError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f"Disqus API error {code}: {message}")
        self.code = code


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in _BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = unescape("".join(parser.parts))
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _default_fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _build_url(module_code: str, api_key: str, forum: str, cursor: str | None) -> str:
    params = {
        "api_key": api_key,
        "forum": forum,
        "thread:ident": module_code,
        "limit": "100",
        "order": "asc",
    }
    if cursor:
        params["cursor"] = cursor
    return _API + "?" + urllib.parse.urlencode(params)


def fetch_reviews(
    module_code: str,
    api_key: str,
    *,
    fetch_json=_default_fetch_json,
    forum: str = "nusmods-prod",
) -> list[Review]:
    reviews: list[Review] = []
    cursor: str | None = None
    while True:
        data = fetch_json(_build_url(module_code, api_key, forum, cursor))
        code = data.get("code", -1)
        if code != 0:
            raise DisqusError(code, str(data.get("response")))
        for post in data.get("response", []):
            if post.get("isDeleted"):
                continue
            reviews.append(
                Review(
                    author=post.get("author", {}).get("name", "anonymous"),
                    created_at=post.get("createdAt", ""),
                    message=html_to_text(post.get("message", "")),
                    likes=post.get("likes", 0),
                )
            )
        cur = data.get("cursor") or {}
        if cur.get("hasNext") and cur.get("next"):
            cursor = cur["next"]
        else:
            return reviews

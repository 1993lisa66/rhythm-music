"""在线歌词查询：LRCLIB 公开接口。

只做「精确匹配才采用」：歌名 + 歌手 + 时长三项由调用方传入，LRCLIB 在时长差超过
±2 秒时不会返回结果。找不到就返回空列表，绝不生成或猜测歌词。

LRCLIB 无需 API Key，但要求客户端带可识别的 User-Agent。
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request

LRCLIB_GET = "https://lrclib.net/api/get"
USER_AGENT = "RhythmMusicApp/1.0 (local music library; contact: demo@localhost)"
TIMEOUT = 12

_LRC_LINE = re.compile(r"^\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\](.*)$")
_META = re.compile(r"^\[(ar|ti|al|by|offset|length|re|ve)\s*:", re.IGNORECASE)


def _lrc_to_lines(raw: str) -> list[dict]:
    lines: list[dict] = []
    for row in raw.splitlines():
        match = _LRC_LINE.match(row.strip())
        if not match:
            continue
        minute, second, fraction, text = match.groups()
        frac = float(f"0.{fraction}") if fraction else 0.0
        t = int(round(int(minute) * 60 + int(second) + frac))
        text = text.strip()
        if text:
            lines.append({"t": t, "text": text})
    return sorted(lines, key=lambda item: item["t"])


def _plain_to_lines(raw: str) -> list[dict]:
    """纯文本歌词没有时间轴，统一 t=0，前端不会错误高亮某一行。"""
    return [{"t": 0, "text": row.strip()} for row in raw.splitlines() if row.strip()]


def fetch_lyrics(title: str, artist: str, duration: int) -> list[dict]:
    """返回 [{t, text}]；未收录或网络失败时返回空列表。"""
    if not title or not artist:
        return []
    query = urllib.parse.urlencode(
        {
            "track_name": title,
            "artist_name": artist,
            "duration": max(1, int(duration or 1)),
        }
    )
    request = urllib.request.Request(
        f"{LRCLIB_GET}?{query}", headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        # 404 = 曲库未收录，属于正常结果；其余错误交给调用方判断是否重试
        if error.code == 404:
            return []
        raise RuntimeError(f"歌词服务返回 HTTP {error.code}") from error
    except Exception as error:  # 网络 / DNS / 超时
        raise RuntimeError(f"歌词服务不可用：{type(error).__name__}") from error

    if payload.get("instrumental"):
        return []
    synced = payload.get("syncedLyrics") or ""
    lines = _lrc_to_lines(synced)
    if not lines:
        lines = _plain_to_lines(payload.get("plainLyrics") or "")
    return lines

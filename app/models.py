"""ORM 模型。

设计原则：歌曲 / 歌单属"内容"，收藏 / 最近播放 / 下载 / 队列 / 播放态属"用户状态"，
两者分表，方便将来接多用户时只给状态表加 user_id。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now_local() -> datetime:
    """统一用服务器本地时间（个人单用户场景，够用且便于按天分组）。"""
    return datetime.now().replace(microsecond=0)


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    artist: Mapped[str] = mapped_column(String(200), index=True)
    album: Mapped[str] = mapped_column(String(200), default="")
    genre: Mapped[str] = mapped_column(String(64), default="", index=True)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    cover: Mapped[str] = mapped_column(String(300), default="")
    added_order: Mapped[int] = mapped_column(Integer, default=0)


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    badge: Mapped[str] = mapped_column(String(64), default="")
    featured_badge: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creator: Mapped[str] = mapped_column(String(120), default="")
    # 策展文案里的数量与时长（与设计稿一致），真实曲目数由 tracks 计算
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_text: Mapped[str] = mapped_column(String(32), default="")
    desc: Mapped[str] = mapped_column(Text, default="")
    info: Mapped[str] = mapped_column(String(200), default="")
    cover: Mapped[str] = mapped_column(String(300), default="")
    tone: Mapped[str] = mapped_column(String(32), default="sunset")
    position: Mapped[int] = mapped_column(Integer, default=0)

    tracks: Mapped[list[PlaylistTrack]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistTrack.position",
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (UniqueConstraint("playlist_id", "position", name="uq_playlist_track_pos"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playlist_id: Mapped[str] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), index=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # 部分曲目在歌单里展示的时长与曲库不同（设计稿数据如此），为空则取曲库时长
    duration_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    playlist: Mapped[Playlist] = relationship(back_populates="tracks")
    song: Mapped[Song] = relationship()


class LyricLine(Base):
    __tablename__ = "lyric_lines"

    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    t: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, default="")


class Favorite(Base):
    __tablename__ = "favorites"

    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class PlayEvent(Base):
    __tablename__ = "play_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    played_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class Download(Base):
    __tablename__ = "downloads"

    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    size: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class QueueItem(Base):
    __tablename__ = "queue_items"

    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)


class PlayerState(Base):
    """单例行（id 恒为 1）。"""

    __tablename__ = "player_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    index: Mapped[int] = mapped_column(Integer, default=0)
    position: Mapped[int] = mapped_column(Integer, default=0)
    playing: Mapped[bool] = mapped_column(default=False)
    shuffle: Mapped[bool] = mapped_column(default=False)
    repeat_mode: Mapped[str] = mapped_column(String(8), default="all")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="null")


class ContentBlock(Base):
    """固定文案（问候语、区块标题、热搜池等）整块存 JSON，避免为每条文案建表。"""

    __tablename__ = "content_blocks"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")

"""ORM 模型。

分两层：
- 内容层：Song / LyricLine / Playlist(+tracks) —— 全用户共享的曲库与歌单模板；
- 用户层：User 以及所有带 user_id 的状态表（收藏 / 播放记录 / 下载 / 队列 / 播放态 / 设置）。

歌单也带 owner_id：注册时会为每个用户克隆一份初始歌单，保证「我的歌单」互相独立；
owner_id 为空表示系统内容（当前未使用，留给后续的编辑精选）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now_local() -> datetime:
    """统一用服务器本地时间（便于按天分组「今天 / 昨天」）。"""
    return datetime.now().replace(microsecond=0)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # 展示用编号，对应设计稿的 “ID: 8823 6102”
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(60), default="")
    password_hash: Mapped[str] = mapped_column(String(200))
    member: Mapped[str] = mapped_column(String(40), default="音乐会员")
    avatar: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    @property
    def public_id(self) -> str:
        raw = f"{self.number:08d}"
        return f"ID: {raw[:4]} {raw[4:]}"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    artist: Mapped[str] = mapped_column(String(200), index=True)
    album: Mapped[str] = mapped_column(String(200), default="")
    genre: Mapped[str] = mapped_column(String(64), default="", index=True)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    cover: Mapped[str] = mapped_column(String(300), default="")
    # OSS 上的音频对象键（如 audio/wanfeng.wav）；空串表示暂无音频，前端退回模拟播放
    audio: Mapped[str] = mapped_column(String(300), default="", server_default="")
    added_order: Mapped[int] = mapped_column(Integer, default=0)


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
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
    playlist_id: Mapped[str] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), index=True
    )
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

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class PlayEvent(Base):
    __tablename__ = "play_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)
    played_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)


class QueueItem(Base):
    __tablename__ = "queue_items"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), index=True)


class PlayerState(Base):
    """每个用户一行，user_id 即主键。"""

    __tablename__ = "player_state"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, default=0)
    position: Mapped[int] = mapped_column(Integer, default=0)
    playing: Mapped[bool] = mapped_column(default=False)
    shuffle: Mapped[bool] = mapped_column(default=False)
    repeat_mode: Mapped[str] = mapped_column(String(8), default="all")


class Setting(Base):
    __tablename__ = "settings"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="null")


class ContentBlock(Base):
    """固定文案（问候语、区块标题、热搜池等）整块存 JSON，避免为每条文案建表。"""

    __tablename__ = "content_blocks"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")

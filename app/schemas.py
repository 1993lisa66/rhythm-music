"""请求 / 响应模型。

响应字段统一 snake_case → camelCase（如 duration_text → durationText），
与前端现有 JSON 的命名保持一致，前端接入时字段名不用改。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# ---------------------------------------------------------------- 内容
class SongOut(CamelModel):
    id: str
    title: str
    artist: str
    album: str
    genre: str
    duration: int
    cover: str
    # 私有 Bucket 的签名播放地址；无音频时为空串
    audio: str = ""
    liked: bool = False


class TrackOut(SongOut):
    index: int = 0


class SongListOut(CamelModel):
    total: int
    items: list[SongOut]


class SongDeleteOut(CamelModel):
    deleted: bool
    song_id: str
    # 成功删除的 OSS 对象数（音频 + 封面，0~2）
    assets_removed: int = 0


class GenreOut(CamelModel):
    name: str
    count: int


class GenreListOut(CamelModel):
    items: list[GenreOut]


class LyricLineOut(CamelModel):
    t: int
    text: str


class LyricsOut(CamelModel):
    song_id: str
    title: str
    has_lyrics: bool
    lines: list[LyricLineOut]


class PlaylistSummary(CamelModel):
    id: str
    title: str
    badge: str
    featured_badge: str | None = None
    creator: str
    # count 为策展文案里的数量（与设计稿一致），track_count 为库中真实曲目数
    count: int
    track_count: int
    duration_text: str
    desc: str
    info: str
    cover: str
    tone: str


class PlaylistDetailOut(PlaylistSummary):
    tracks: list[TrackOut]
    # 是否是当前登录用户自己的歌单（决定前端是否显示编辑 / 删除入口）
    owned: bool = False


class PlaylistListOut(CamelModel):
    total: int
    items: list[PlaylistSummary]


class PlaylistCreateIn(CamelModel):
    title: str = Field(min_length=1, max_length=60)
    desc: str = Field(default="", max_length=300)


class PlaylistUpdateIn(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    desc: str | None = Field(default=None, max_length=300)


class PlaylistTracksIn(CamelModel):
    song_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- 播放器
class PlayerOut(CamelModel):
    playing: bool
    shuffle: bool
    repeat: str
    index: int
    position: int
    position_text: str
    duration: int
    duration_text: str
    progress: float
    current: SongOut | None = None
    queue: list[SongOut] = Field(default_factory=list)
    liked: bool = False


class QueueOut(CamelModel):
    total: int
    items: list[TrackOut]


class PlayRequest(CamelModel):
    song_id: str
    queue_ids: list[str] | None = None


class SeekRequest(CamelModel):
    position: int | None = None
    ratio: float | None = None


class ProgressRequest(CamelModel):
    position: int | None = None
    ratio: float | None = None
    playing: bool | None = None


class QueueAddRequest(CamelModel):
    song_ids: list[str]


class ShuffleRequest(CamelModel):
    enabled: bool | None = None


class RepeatRequest(CamelModel):
    mode: Literal["all", "one", "off"] | None = None


# ---------------------------------------------------------------- 搜索
class HotItem(CamelModel):
    text: str
    tone: str


class HotOut(CamelModel):
    title: str
    refresh: str
    placeholder: str
    cancel: str
    items: list[HotItem]


class RecommendItem(CamelModel):
    id: str
    title: str
    sub: str = ""
    cover: str
    # 卡片尺寸：lg 为大卡（320×150 那一排），sm 为小卡
    size: str = "sm"


class RecommendOut(CamelModel):
    title: str
    items: list[RecommendItem]


class ArtistOut(CamelModel):
    name: str
    song_count: int
    cover: str


class SearchOut(CamelModel):
    query: str
    total: int
    songs: list[SongOut]
    playlists: list[PlaylistSummary]
    artists: list[ArtistOut]


class SuggestOut(CamelModel):
    query: str
    items: list[str]


# ---------------------------------------------------------------- 最近播放
class RecentItem(SongOut):
    played_at: datetime | None = None


class RecentGroup(CamelModel):
    label: str
    count: int
    items: list[RecentItem]


class RecentOut(CamelModel):
    title: str
    total: int
    groups: list[RecentGroup]


class RecordOut(CamelModel):
    recorded: bool
    song_id: str
    played_at: datetime


class ClearOut(CamelModel):
    cleared: bool


class FavoriteStateOut(CamelModel):
    song_id: str
    liked: bool
    total: int


class FavoriteListOut(CamelModel):
    total: int
    items: list[SongOut]


# ---------------------------------------------------------------- 下载
class DownloadItem(SongOut):
    size: str
    downloaded_at: datetime | None = None


class DownloadListOut(CamelModel):
    total: int
    total_size: str
    items: list[DownloadItem]


class DownloadCreate(CamelModel):
    song_id: str
    size: str | None = None


# ---------------------------------------------------------------- 账号
class UserOut(CamelModel):
    # id 是展示用编号（对应设计稿 “ID: 8823 6102”），真正的用户主键不出现在响应里
    id: str
    email: str
    name: str
    member: str
    avatar: str


class TokenOut(CamelModel):
    token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RegisterIn(CamelModel):
    email: str
    password: str
    name: str | None = None


class LoginIn(CamelModel):
    email: str
    password: str


class AccountPatch(CamelModel):
    name: str | None = None
    avatar: str | None = None


class OkOut(CamelModel):
    ok: bool


# ---------------------------------------------------------------- 我的
class StatOut(CamelModel):
    value: str
    label: str


class MenuItemOut(CamelModel):
    icon: str
    name: str
    value: str
    route: str
    count: int


class MenuOut(CamelModel):
    title: str
    items: list[MenuItemOut]


class ComputedOut(CamelModel):
    favorites: int
    playlists: int
    songs: int
    downloads: int
    today_plays: int
    # 关注数没有数据源，暂为 None
    following: int | None = None


class ProfileOut(CamelModel):
    title: str
    user: UserOut
    stats: list[StatOut]
    menu: MenuOut
    computed: ComputedOut


class SettingsOut(CamelModel):
    quality: str
    qualities: list[str]
    wifi_only: bool
    show_lyrics: bool


class SettingsPatch(CamelModel):
    quality: Literal["标准", "高品质", "无损"] | None = None
    wifi_only: bool | None = None
    show_lyrics: bool | None = None


# ---------------------------------------------------------------- 发现 / 乐库
class MoodOut(CamelModel):
    name: str
    tone: str
    genre: str


class FeatureOut(CamelModel):
    section_title: str
    more: str
    playlist: PlaylistSummary | None = None


class DiscoverSectionOut(CamelModel):
    title: str
    more: str
    items: list[SongOut]


class MoodSectionOut(CamelModel):
    title: str
    items: list[MoodOut]


class DiscoverOut(CamelModel):
    greeting: str
    headline: str
    search_placeholder: str
    featured: FeatureOut
    moods: MoodSectionOut
    recent: DiscoverSectionOut


class AlbumOut(CamelModel):
    name: str
    artist: str
    cover: str
    song_count: int
    duration: int
    track_ids: list[str]


class AlbumListOut(CamelModel):
    total: int
    items: list[AlbumOut]


class LibraryPlaylistsOut(CamelModel):
    title: str
    items: list[PlaylistSummary]


class LibraryOut(CamelModel):
    title: str
    search_placeholder: str
    tabs: list[str]
    recent: DiscoverSectionOut
    playlists: LibraryPlaylistsOut


class HealthOut(CamelModel):
    status: str
    version: str
    songs: int
    playlists: int
    users: int = 0


class SignIn(CamelModel):
    """换签入参：对象键或完整的旧签名地址都可以，前端不必自己拆 query。"""

    paths: list[str] = []


class SignedAsset(CamelModel):
    key: str
    url: str
    expires_at: int


class SignOut(CamelModel):
    items: list[SignedAsset]
    expires_at: int
    ttl: int

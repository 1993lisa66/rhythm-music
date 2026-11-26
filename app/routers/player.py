"""播放器与队列。所有写接口都直接返回完整播放态，前端一次请求即可同步 UI。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..errors import bad_request, not_found
from ..models import QueueItem, Song
from ..schemas import (
    PlayerOut,
    PlayRequest,
    ProgressRequest,
    QueueAddRequest,
    QueueOut,
    RepeatRequest,
    SeekRequest,
    ShuffleRequest,
)
from ..services import (
    advance_next,
    advance_prev,
    current_duration,
    favorite_ids,
    get_player,
    get_song,
    player_payload,
    queue_ids,
    queue_songs,
    record_play,
    rewrite_queue,
    seek_to,
    set_queue,
    song_out,
)

router = APIRouter(tags=["player"])


def _record_current(db: Session) -> None:
    payload = player_payload(db)
    current = payload.get("current")
    if current:
        record_play(db, current["id"])


@router.get("/player", response_model=PlayerOut, summary="当前播放态 + 队列")
def read_player(db: Session = Depends(get_db)) -> dict:
    return player_payload(db)


@router.post("/player/play", response_model=PlayerOut, summary="播放指定歌曲（可同时重置队列）")
def play(body: PlayRequest, db: Session = Depends(get_db)) -> dict:
    get_song(db, body.song_id)

    if body.queue_ids:
        ids = [song_id for song_id in body.queue_ids if db.get(Song, song_id) is not None]
        if body.song_id not in ids:
            ids.insert(0, body.song_id)
        set_queue(db, ids, start_index=ids.index(body.song_id), autoplay=True)
    else:
        ids = queue_ids(db)
        state = get_player(db)
        if body.song_id in ids:
            state.index = ids.index(body.song_id)
            state.position = 0
            state.playing = True
            db.commit()
        else:
            db.add(QueueItem(position=len(ids), song_id=body.song_id))
            db.commit()
            state = get_player(db)
            state.index = len(ids)
            state.position = 0
            state.playing = True
            db.commit()

    record_play(db, body.song_id)
    return player_payload(db)


@router.post("/player/pause", response_model=PlayerOut, summary="暂停")
def pause(db: Session = Depends(get_db)) -> dict:
    state = get_player(db)
    state.playing = False
    db.commit()
    return player_payload(db)


@router.post("/player/resume", response_model=PlayerOut, summary="继续播放")
def resume(db: Session = Depends(get_db)) -> dict:
    state = get_player(db)
    if current_duration(db) > 0:
        state.playing = True
    db.commit()
    return player_payload(db)


@router.post("/player/toggle", response_model=PlayerOut, summary="播放 / 暂停切换")
def toggle(db: Session = Depends(get_db)) -> dict:
    state = get_player(db)
    state.playing = not state.playing
    db.commit()
    return player_payload(db)


@router.post("/player/next", response_model=PlayerOut, summary="下一首")
def next_track(auto: bool = False, db: Session = Depends(get_db)) -> dict:
    payload = advance_next(db, auto=auto)
    _record_current(db)
    return payload


@router.post("/player/prev", response_model=PlayerOut, summary="上一首")
def prev_track(db: Session = Depends(get_db)) -> dict:
    payload = advance_prev(db)
    _record_current(db)
    return payload


@router.post("/player/seek", response_model=PlayerOut, summary="跳转进度（秒或比例）")
def seek(body: SeekRequest, db: Session = Depends(get_db)) -> dict:
    if body.position is None and body.ratio is None:
        raise bad_request("position 与 ratio 至少提供一个")
    return seek_to(db, position=body.position, ratio=body.ratio)


@router.put("/player/progress", response_model=PlayerOut, summary="上报播放进度（客户端驱动）")
def progress(body: ProgressRequest, db: Session = Depends(get_db)) -> dict:
    payload = seek_to(db, position=body.position, ratio=body.ratio)
    if body.playing is not None:
        state = get_player(db)
        state.playing = body.playing
        db.commit()
        payload = player_payload(db)
    return payload


@router.post("/player/shuffle", response_model=PlayerOut, summary="随机播放开关（不传则取反）")
def toggle_shuffle(body: ShuffleRequest | None = None, db: Session = Depends(get_db)) -> dict:
    state = get_player(db)
    state.shuffle = body.enabled if body and body.enabled is not None else not state.shuffle
    db.commit()
    return player_payload(db)


@router.post("/player/repeat", response_model=PlayerOut, summary="循环模式 all / one / off")
def change_repeat(body: RepeatRequest | None = None, db: Session = Depends(get_db)) -> dict:
    state = get_player(db)
    if body and body.mode:
        state.repeat_mode = body.mode
    else:
        order = ["all", "one", "off"]
        state.repeat_mode = order[(order.index(state.repeat_mode) + 1) % len(order)]
    db.commit()
    return player_payload(db)


@router.get("/player/queue", response_model=QueueOut, summary="播放队列")
def read_queue(db: Session = Depends(get_db)) -> dict:
    liked = favorite_ids(db)
    songs = queue_songs(db)
    return {
        "total": len(songs),
        "items": [dict(song_out(song, liked), index=index) for index, song in enumerate(songs)],
    }


@router.post("/player/queue", response_model=QueueOut, summary="追加到队列（自动去重）")
def add_to_queue(body: QueueAddRequest, db: Session = Depends(get_db)) -> dict:
    ids = queue_ids(db)
    for song_id in body.song_ids:
        if db.get(Song, song_id) is not None and song_id not in ids:
            ids.append(song_id)

    state = get_player(db)
    rewrite_queue(db, ids, state.index, state.position, state.playing)

    liked = favorite_ids(db)
    songs = queue_songs(db)
    return {
        "total": len(songs),
        "items": [dict(song_out(song, liked), index=index) for index, song in enumerate(songs)],
    }


@router.delete("/player/queue", response_model=PlayerOut, summary="清空队列（保留当前曲）")
def clear_queue(db: Session = Depends(get_db)) -> dict:
    ids = queue_ids(db)
    if not ids:
        return player_payload(db)

    state = get_player(db)
    keep = ids[min(state.index, len(ids) - 1)]
    rewrite_queue(db, [keep], 0, 0, state.playing)
    return player_payload(db)


@router.delete("/player/queue/{position}", response_model=PlayerOut, summary="从队列移除一项")
def remove_from_queue(position: int, db: Session = Depends(get_db)) -> dict:
    ids = queue_ids(db)
    if len(ids) <= 1:
        raise bad_request("队列至少保留一首")
    if position < 0 or position >= len(ids):
        raise not_found(f"队列位置不存在：{position}", code="queue_position_not_found")

    state = get_player(db)
    index = state.index
    offset = state.position
    playing = state.playing

    ids.pop(position)
    if position < index:
        index -= 1
    elif position == index:
        index = min(index, len(ids) - 1)
        offset = 0

    rewrite_queue(db, ids, index, offset, playing)
    return player_payload(db)

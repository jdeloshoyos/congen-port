"""Small audio manager: SFX pool + optional looping music."""

from __future__ import annotations

from .assets import Assets
from .config import Config


class Audio:
    def __init__(self, assets: Assets, cfg: Config):
        self.assets = assets
        self.cfg = cfg
        self.sfx: list = []
        self.music_player = None

    def play(self, sid: int) -> None:
        if not self.cfg.sfx_on:
            return
        src = self.assets.sounds.get(sid)
        if src is None:
            return
        try:
            p = src.play()
            p.volume = self.cfg.sfx_volume
            self.sfx.append(p)
        except Exception:
            pass

    def play_all(self, ids) -> None:
        for sid in ids:
            self.play(sid)

    def _stop_music(self) -> None:
        if self.music_player is not None:
            try:
                self.music_player.delete()
            except Exception:
                pass
            self.music_player = None

    def refresh_music(self) -> None:
        if self.cfg.music_on and self.assets.music is not None:
            if self.music_player is None:
                try:
                    p = self.assets.music.play()
                    p.loop = True
                    p.volume = self.cfg.music_volume
                    self.music_player = p
                except Exception:
                    self.music_player = None
        else:
            self._stop_music()

    def update(self) -> None:
        if self.sfx:
            self.sfx = [p for p in self.sfx if p.playing]

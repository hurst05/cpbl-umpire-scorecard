from typing import Literal, get_args

GameKind = Literal["A", "G", "E", "C"]
SUPPORTED_KIND_CODES = get_args(GameKind)


def get_game_kind(game: dict) -> str | None:
    parts = (game.get("game_id") or "").split("-")
    return game.get("kind_code") or (parts[1] if len(parts) == 3 else None)

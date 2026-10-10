export const GAME_TYPES = {
  A: '一軍例行賽',
  G: '一軍熱身賽',
  E: '一軍季後挑戰賽',
  C: '一軍總冠軍賽'
}

export function getGameKindCode(game) {
  return game?.kind_code || game?.game_id?.split('-')[1]
}

export function filterGamesByKind(games, kindCode = 'A') {
  return games.filter(game => getGameKindCode(game) === kindCode)
}

/**
 * CPBL 中華職棒各球團標準代表色與配色設定
 */
export const CPBL_TEAMS = {
  '中信兄弟': {
    name: '中信兄弟',
    primary: '#EAAA00', // 兄弟金黃
    secondary: '#002B49',
    pitchColor: '#EAB308',
    badgeBg: 'rgba(234, 179, 8, 0.15)',
    badgeBorder: 'rgba(234, 179, 8, 0.45)',
    badgeText: '#a16207',
    darkBadgeText: '#facc15'
  },
  '統一7-ELEVEn獅': {
    name: '統一7-ELEVEn獅',
    primary: '#EA580C', // 統一橘
    secondary: '#004F32',
    pitchColor: '#F97316',
    badgeBg: 'rgba(249, 115, 22, 0.15)',
    badgeBorder: 'rgba(249, 115, 22, 0.45)',
    badgeText: '#c2410c',
    darkBadgeText: '#fb923c'
  },
  '統一獅': {
    name: '統一獅',
    primary: '#EA580C',
    secondary: '#004F32',
    pitchColor: '#F97316',
    badgeBg: 'rgba(249, 115, 22, 0.15)',
    badgeBorder: 'rgba(249, 115, 22, 0.45)',
    badgeText: '#c2410c',
    darkBadgeText: '#fb923c'
  },
  '樂天桃猿': {
    name: '樂天桃猿',
    primary: '#881337', // 桃猿酒紅
    secondary: '#C5A059',
    pitchColor: '#BE123C',
    badgeBg: 'rgba(190, 18, 60, 0.15)',
    badgeBorder: 'rgba(190, 18, 60, 0.45)',
    badgeText: '#9f1239',
    darkBadgeText: '#f43f5e'
  },
  '味全龍': {
    name: '味全龍',
    primary: '#DC2626', // 烈焰紅
    secondary: '#000000',
    pitchColor: '#EF4444',
    badgeBg: 'rgba(239, 68, 68, 0.15)',
    badgeBorder: 'rgba(239, 68, 68, 0.45)',
    badgeText: '#b91c1c',
    darkBadgeText: '#f87171'
  },
  '富邦悍將': {
    name: '富邦悍將',
    primary: '#0284C7', // 悍將藍
    secondary: '#002D62',
    pitchColor: '#0EA5E9',
    badgeBg: 'rgba(14, 165, 233, 0.15)',
    badgeBorder: 'rgba(14, 165, 233, 0.45)',
    badgeText: '#0369a1',
    darkBadgeText: '#38bdf8'
  },
  '台鋼雄鷹': {
    name: '台鋼雄鷹',
    primary: '#0D9488', // 雄鷹綠
    secondary: '#F5A623',
    pitchColor: '#14B8A6',
    badgeBg: 'rgba(20, 184, 166, 0.15)',
    badgeBorder: 'rgba(20, 184, 166, 0.45)',
    badgeText: '#0f766e',
    darkBadgeText: '#2dd4bf'
  }
}

/**
 * 依球隊名稱模糊匹配球隊代表配色資訊
 * @param {string} teamName 
 * @returns {object} 配色設定物件
 */
export function getTeamColorInfo(teamName) {
  if (!teamName || typeof teamName !== 'string') {
    return {
      primary: '#64748B',
      secondary: '#334155',
      pitchColor: '#64748B',
      badgeBg: 'rgba(100, 116, 139, 0.15)',
      badgeBorder: 'rgba(100, 116, 139, 0.4)',
      badgeText: '#475569',
      darkBadgeText: '#94a3b8'
    }
  }

  for (const [key, val] of Object.entries(CPBL_TEAMS)) {
    if (teamName.includes(key) || key.includes(teamName)) {
      return val
    }
  }

  if (teamName.includes('兄弟') || teamName.includes('中信')) return CPBL_TEAMS['中信兄弟']
  if (teamName.includes('統一') || teamName.includes('獅')) return CPBL_TEAMS['統一獅']
  if (teamName.includes('樂天') || teamName.includes('桃猿') || teamName.includes('猿')) return CPBL_TEAMS['樂天桃猿']
  if (teamName.includes('味全') || teamName.includes('龍')) return CPBL_TEAMS['味全龍']
  if (teamName.includes('富邦') || teamName.includes('悍將')) return CPBL_TEAMS['富邦悍將']
  if (teamName.includes('台鋼') || teamName.includes('雄鷹') || teamName.includes('鷹')) return CPBL_TEAMS['台鋼雄鷹']

  return {
    primary: '#3B82F6',
    secondary: '#1D4ED8',
    pitchColor: '#3B82F6',
    badgeBg: 'rgba(59, 130, 246, 0.15)',
    badgeBorder: 'rgba(59, 130, 246, 0.4)',
    badgeText: '#1d4ed8',
    darkBadgeText: '#60a5fa'
  }
}

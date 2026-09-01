/**
 * CPBL 打者投打習慣對照表與輔助工具
 * 'L': 左打 (Left-handed)
 * 'R': 右打 (Right-handed)
 * 'S': 左右開弓 / 兩打 (Switch)
 */

export const CPBL_BATTERS_BATS = {
  // === 統一 7-ELEVEn 獅 ===
  '邱智呈': 'L',
  '陳傑憲': 'L',
  '蘇智傑': 'L',
  '林安可': 'L',
  '潘傑楷': 'L',
  '陳重廷': 'R',
  '陳重羽': 'R',
  '林岱安': 'R',
  '林祖傑': 'R',
  '許哲晏': 'R',
  '黃勇傳': 'L',
  '林佳緯': 'L',
  '張偉聖': 'L',
  '柯育民': 'R',
  '胡金龍': 'R',
  '陳鏞基': 'R',
  '林益全': 'L',
  '唐肇廷': 'L',
  '田子杰': 'L',
  '張皓崴': 'S',
  '楊竣翔': 'R',
  '林泓弦': 'R',
  '羅暐捷': 'L',
  '何恆佑': 'L',

  // === 中信兄弟 ===
  '岳政華': 'L',
  '江坤宇': 'R',
  '岳東華': 'L',
  '許基宏': 'L',
  '陳子豪': 'L',
  '王威晨': 'L',
  '詹子賢': 'R',
  '曾頌恩': 'R',
  '高宇杰': 'R',
  '徐博瑋': 'R',
  '陳統恩': 'R',
  '張仁瑋': 'R',
  '林吳晉瑋': 'L',
  '王政順': 'L',
  '蘇緯達': 'L',
  '周思齊': 'L',
  '宋晟睿': 'R',
  '馬鋼': 'R',
  '黃韋盛': 'R',
  '楊祥禾': 'R',
  '林書逸': 'L',
  '潘志芳': 'L',

  // === 樂天桃猿 ===
  '林立': 'R',
  '陳晨威': 'L',
  '梁家榮': 'L',
  '廖健富': 'L',
  '朱育賢': 'L',
  '林承飛': 'R',
  '林智平': 'R',
  '馮健庭': 'R',
  '嚴宏鈞': 'L',
  '張閔勛': 'R',
  '余德龍': 'R',
  '林泓育': 'R',
  '邱丹': 'L',
  '馬傑森': 'R',
  '李勛傑': 'R',
  '杜禹鋒': 'R',
  '鐘玉成': 'R',
  '毛英傑': 'R',
  '宋嘉翔': 'L',
  '林政華': 'L',

  // === 味全龍 ===
  '李凱威': 'L',
  '吉力吉撈．鞏冠': 'R',
  '吉力吉撈·鞏冠': 'R',
  '吉力吉撈': 'R',
  '劉基鴻': 'R',
  '郭天信': 'L',
  '張祐銘': 'L',
  '陳品捷': 'L',
  '林孝程': 'L',
  '拿莫．伊漾': 'R',
  '拿莫·伊漾': 'R',
  '蔣少宏': 'R',
  '劉時豪': 'L',
  '張政禹': 'L',
  '瑪仕革斯．俄霸律尼': 'L',
  '瑪仕革斯·俄霸律尼': 'L',
  '王順和': 'R',
  '冉承霖': 'L',
  '石翔宇': 'R',
  '黃柏豪': 'L',
  '曾陶鎔': 'R',
  '鄭鎧文': 'R',
  '林辰勳': 'R',
  '全浩瑋': 'R',

  // === 富邦悍將 ===
  '李宗賢': 'R',
  '王正棠': 'L',
  '申皓瑋': 'R',
  '范國宸': 'R',
  '張育成': 'R',
  '戴培峰': 'L',
  '高捷': 'L',
  '董子恩': 'R',
  '池恩齊': 'L',
  '陳真': 'R',
  '孔念恩': 'L',
  '周佳樂': 'L',
  '葉子霆': 'R',
  '王勝偉': 'R',
  '蔣智賢': 'L',
  '林哲瑄': 'R',
  '張進德': 'L',
  '姚冠瑋': 'R',
  '辛元旭': 'R',
  '豊暐': 'R',
  '張冠廷': 'L',
  '蔡佳諺': 'R',

  // === 台鋼雄鷹 ===
  '曾子祐': 'R',
  '陳文杰': 'L',
  '王柏融': 'L',
  '魔鷹': 'L',
  '杜家明': 'R',
  '藍寅倫': 'L',
  '張肇元': 'R',
  '吳明鴻': 'R',
  '葉保弟': 'L',
  '紀慶然': 'L',
  '黃劼妤': 'R',
  '胡冠俞': 'R',
  '郭永維': 'R',
  '孫易伸': 'R',
  '高聖恩': 'R',
  '王博玄': 'L',
  '洪瑋漢': 'L',
  '陳飛霖': 'L',
  '林家鋐': 'L',
  '顏清浤': 'L'
}

/**
 * 標準化打擊習慣字串
 */
export function normalizeBats(str) {
  if (!str) return 'R'
  const upper = String(str).toUpperCase()
  if (upper === 'L' || upper === 'LEFT' || upper.includes('左')) return 'L'
  if (upper === 'S' || upper === 'SWITCH' || upper.includes('兩') || upper.includes('雙') || upper.includes('左右')) return 'S'
  return 'R'
}

/**
 * 取得打者的打擊站位習慣 ('L' | 'R' | 'S')
 * @param {object|string} batterOrPitch 
 * @returns {'L'|'R'|'S'}
 */
export function getBatterBats(batterOrPitch) {
  if (!batterOrPitch) return 'R'

  // 1. 若物件本身已有標註 bats / batter_bats
  if (typeof batterOrPitch === 'object') {
    if (batterOrPitch.bats) return normalizeBats(batterOrPitch.bats)
    if (batterOrPitch.batter_bats) return normalizeBats(batterOrPitch.batter_bats)
    if (batterOrPitch.batter?.bats) return normalizeBats(batterOrPitch.batter.bats)
  }

  // 2. 從打者姓名查詢
  let name = ''
  if (typeof batterOrPitch === 'string') {
    name = batterOrPitch
  } else if (typeof batterOrPitch.batter === 'string') {
    name = batterOrPitch.batter
  } else if (batterOrPitch.batter?.name) {
    name = batterOrPitch.batter.name
  } else if (batterOrPitch.name) {
    name = batterOrPitch.name
  }

  const cleanName = name.replace(/^[#\s]+/, '').replace(/[\s\d]+$/, '').trim()
  if (cleanName && CPBL_BATTERS_BATS[cleanName]) {
    return CPBL_BATTERS_BATS[cleanName]
  }

  return 'R'
}

/**
 * 取得打席中文標籤 (例如 "左打", "右打", "左右開弓")
 * @param {object|string} batterOrPitch 
 * @returns {string}
 */
export function getBatterBatsLabel(batterOrPitch) {
  const bats = getBatterBats(batterOrPitch)
  if (bats === 'L') return '左打'
  if (bats === 'S') return '兩打'
  return '右打'
}

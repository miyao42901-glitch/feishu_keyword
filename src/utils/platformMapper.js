/**
 * Platform code to Chinese name mapping
 */
export const platformNameMap = {
  douyin: '抖音',
  xhs: '小红书',
  wx: '视频号',
  mp: '公众号',
  ks: '快手'
};

/**
 * Map platform code to Chinese name
 * @param {string} platformCode - Platform code (e.g., 'douyin', 'xhs')
 * @returns {string} Chinese platform name
 */
export function getPlatformName(platformCode) {
  return platformNameMap[platformCode] || platformCode;
}

/**
 * Transform API response platform stats with Chinese names
 * @param {Array} platformStats - Array of platform statistics
 * @returns {Array} Transformed platform stats with Chinese names
 */
export function transformPlatformStats(platformStats) {
  if (!Array.isArray(platformStats)) return [];
  
  return platformStats.map(stat => ({
    ...stat,
    platformName: getPlatformName(stat.platform),
    platform: stat.platform
  }));
}

/**
 * Transform API response records with Chinese platform names
 * @param {Array} records - Array of API call records
 * @returns {Array} Transformed records with Chinese platform names
 */
export function transformApiRecords(records) {
  if (!Array.isArray(records)) return [];
  
  return records.map(record => ({
    ...record,
    platformName: getPlatformName(record.platform),
    platform: record.platform
  }));
}

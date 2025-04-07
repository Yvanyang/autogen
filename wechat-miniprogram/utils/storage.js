/**
 * 本地存储工具
 * 封装微信小程序的本地存储API，提供更便捷的使用方式
 */

const STORAGE_PREFIX = 'CHAT_APP_';

const DEFAULT_EXPIRES = 7 * 24 * 60 * 60 * 1000;

/**
 * 设置存储
 * @param {string} key - 存储键
 * @param {any} value - 存储值
 * @param {number} [expires=DEFAULT_EXPIRES] - 过期时间（毫秒）
 * @returns {boolean} 是否成功
 */
const set = (key, value, expires = DEFAULT_EXPIRES) => {
  if (!key) return false;
  
  const data = {
    value,
    expires: expires ? Date.now() + expires : null
  };
  
  try {
    wx.setStorageSync(STORAGE_PREFIX + key, JSON.stringify(data));
    return true;
  } catch (e) {
    console.error('Storage set error:', e);
    return false;
  }
};

/**
 * 获取存储
 * @param {string} key - 存储键
 * @param {any} [defaultValue=null] - 默认值
 * @returns {any} 存储值或默认值
 */
const get = (key, defaultValue = null) => {
  if (!key) return defaultValue;
  
  try {
    const data = wx.getStorageSync(STORAGE_PREFIX + key);
    if (!data) return defaultValue;
    
    const parsedData = JSON.parse(data);
    
    if (parsedData.expires && parsedData.expires < Date.now()) {
      remove(key);
      return defaultValue;
    }
    
    return parsedData.value;
  } catch (e) {
    console.error('Storage get error:', e);
    return defaultValue;
  }
};

/**
 * 移除存储
 * @param {string} key - 存储键
 * @returns {boolean} 是否成功
 */
const remove = (key) => {
  if (!key) return false;
  
  try {
    wx.removeStorageSync(STORAGE_PREFIX + key);
    return true;
  } catch (e) {
    console.error('Storage remove error:', e);
    return false;
  }
};

/**
 * 清除所有存储
 * @returns {boolean} 是否成功
 */
const clear = () => {
  try {
    const res = wx.getStorageInfoSync();
    const keys = res.keys;
    
    keys.forEach(key => {
      if (key.startsWith(STORAGE_PREFIX)) {
        wx.removeStorageSync(key);
      }
    });
    
    return true;
  } catch (e) {
    console.error('Storage clear error:', e);
    return false;
  }
};

/**
 * 获取存储信息
 * @returns {Object} 存储信息
 */
const info = () => {
  try {
    return wx.getStorageInfoSync();
  } catch (e) {
    console.error('Storage info error:', e);
    return {};
  }
};

module.exports = {
  set,
  get,
  remove,
  clear,
  info
};

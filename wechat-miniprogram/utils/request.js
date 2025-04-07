/**
 * 网络请求工具
 * 封装微信小程序的wx.request API，提供更便捷的使用方式
 */

const BASE_URL = 'https://api.example.com';

const HTTP_METHOD = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE'
};

const TIMEOUT = 30000;

let requestQueue = [];

let showLoading = true;

/**
 * 发起网络请求
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求URL，可以是相对路径或完整URL
 * @param {string} [options.method='GET'] - 请求方法
 * @param {Object} [options.data={}] - 请求数据
 * @param {Object} [options.header={}] - 请求头
 * @param {boolean} [options.loading=true] - 是否显示加载提示
 * @param {number} [options.timeout=30000] - 超时时间
 * @returns {Promise} 返回Promise对象
 */
const request = (options = {}) => {
  const config = {
    url: options.url,
    method: options.method || HTTP_METHOD.GET,
    data: options.data || {},
    header: {
      'content-type': 'application/json',
      ...options.header
    },
    timeout: options.timeout || TIMEOUT
  };

  if (!config.url.startsWith('http')) {
    config.url = BASE_URL + config.url;
  }

  showLoading = options.loading !== false;

  if (showLoading && requestQueue.length === 0) {
    wx.showLoading({
      title: '加载中...',
      mask: true
    });
  }

  requestQueue.push(config.url);

  return new Promise((resolve, reject) => {
    wx.request({
      ...config,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const error = {
            code: res.statusCode,
            message: res.data.message || '请求失败',
            data: res.data
          };
          reject(error);
          
          wx.showToast({
            title: error.message,
            icon: 'none',
            duration: 2000
          });
        }
      },
      fail: (err) => {
        const error = {
          code: -1,
          message: err.errMsg || '网络异常',
          data: err
        };
        reject(error);
        
        wx.showToast({
          title: error.message,
          icon: 'none',
          duration: 2000
        });
      },
      complete: () => {
        const index = requestQueue.indexOf(config.url);
        if (index > -1) {
          requestQueue.splice(index, 1);
        }
        
        if (showLoading && requestQueue.length === 0) {
          wx.hideLoading();
        }
      }
    });
  });
};

/**
 * GET请求
 * @param {string} url - 请求URL
 * @param {Object} [data={}] - 请求数据
 * @param {Object} [options={}] - 其他配置
 * @returns {Promise} 返回Promise对象
 */
const get = (url, data = {}, options = {}) => {
  return request({
    url,
    method: HTTP_METHOD.GET,
    data,
    ...options
  });
};

/**
 * POST请求
 * @param {string} url - 请求URL
 * @param {Object} [data={}] - 请求数据
 * @param {Object} [options={}] - 其他配置
 * @returns {Promise} 返回Promise对象
 */
const post = (url, data = {}, options = {}) => {
  return request({
    url,
    method: HTTP_METHOD.POST,
    data,
    ...options
  });
};

/**
 * PUT请求
 * @param {string} url - 请求URL
 * @param {Object} [data={}] - 请求数据
 * @param {Object} [options={}] - 其他配置
 * @returns {Promise} 返回Promise对象
 */
const put = (url, data = {}, options = {}) => {
  return request({
    url,
    method: HTTP_METHOD.PUT,
    data,
    ...options
  });
};

/**
 * DELETE请求
 * @param {string} url - 请求URL
 * @param {Object} [data={}] - 请求数据
 * @param {Object} [options={}] - 其他配置
 * @returns {Promise} 返回Promise对象
 */
const del = (url, data = {}, options = {}) => {
  return request({
    url,
    method: HTTP_METHOD.DELETE,
    data,
    ...options
  });
};

module.exports = {
  request,
  get,
  post,
  put,
  delete: del
};

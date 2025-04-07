/**
 * 权限管理工具
 * 封装微信小程序的权限相关API，提供更便捷的使用方式
 */

const PERMISSION_TYPE = {
  USERINFO: 'scope.userInfo',
  USERPROFILE: 'scope.userProfile',
  USERADDRESS: 'scope.address',
  USERPHONE: 'scope.phoneNumber',
  USERLOCATION: 'scope.userLocation',
  CAMERA: 'scope.camera',
  RECORD: 'scope.record',
  ALBUM: 'scope.writePhotosAlbum',
  INVOICE: 'scope.invoice',
  INVOICE_TITLE: 'scope.invoiceTitle',
  WERUN: 'scope.werun',
  BLUETOOTH: 'scope.bluetooth',
  CALENDAR: 'scope.calendar'
};

/**
 * 检查权限状态
 * @param {string} permissionType - 权限类型
 * @returns {Promise} 返回Promise对象，resolve为权限状态
 */
const checkPermission = (permissionType) => {
  return new Promise((resolve, reject) => {
    wx.getSetting({
      success: (res) => {
        resolve({
          granted: res.authSetting[permissionType] === true,
          denied: res.authSetting[permissionType] === false,
          unknown: res.authSetting[permissionType] === undefined
        });
      },
      fail: reject
    });
  });
};

/**
 * 请求权限
 * @param {string} permissionType - 权限类型
 * @param {string} [reason=''] - 请求权限的原因
 * @returns {Promise} 返回Promise对象，resolve为是否授权
 */
const requestPermission = (permissionType, reason = '') => {
  return new Promise(async (resolve, reject) => {
    try {
      const status = await checkPermission(permissionType);
      
      if (status.granted) {
        resolve(true);
        return;
      }
      
      if (status.denied) {
        const confirmed = await showPermissionDialog(permissionType, reason);
        if (confirmed) {
          wx.openSetting({
            success: (res) => {
              resolve(res.authSetting[permissionType] === true);
            },
            fail: reject
          });
        } else {
          resolve(false);
        }
        return;
      }
      
      if (permissionType === PERMISSION_TYPE.USERINFO) {
        wx.getUserProfile({
          desc: reason || '用于完善会员资料',
          success: () => {
            resolve(true);
          },
          fail: () => {
            resolve(false);
          }
        });
      } else if (permissionType === PERMISSION_TYPE.USERLOCATION) {
        wx.getLocation({
          success: () => {
            resolve(true);
          },
          fail: () => {
            resolve(false);
          }
        });
      } else if (permissionType === PERMISSION_TYPE.ALBUM) {
        wx.saveImageToPhotosAlbum({
          filePath: '', // 需要一个有效的图片路径
          success: () => {
            resolve(true);
          },
          fail: () => {
            resolve(false);
          }
        });
      } else if (permissionType === PERMISSION_TYPE.CAMERA) {
        wx.chooseImage({
          count: 1,
          sourceType: ['camera'],
          success: () => {
            resolve(true);
          },
          fail: () => {
            resolve(false);
          }
        });
      } else {
        wx.authorize({
          scope: permissionType,
          success: () => {
            resolve(true);
          },
          fail: () => {
            resolve(false);
          }
        });
      }
    } catch (err) {
      reject(err);
    }
  });
};

/**
 * 显示权限对话框
 * @param {string} permissionType - 权限类型
 * @param {string} [reason=''] - 请求权限的原因
 * @returns {Promise} 返回Promise对象，resolve为是否确认
 */
const showPermissionDialog = (permissionType, reason = '') => {
  const permissionName = getPermissionName(permissionType);
  
  const message = reason || `需要您授权${permissionName}权限才能使用此功能`;
  
  return new Promise((resolve) => {
    wx.showModal({
      title: '权限申请',
      content: message,
      confirmText: '去设置',
      cancelText: '取消',
      success: (res) => {
        resolve(res.confirm);
      }
    });
  });
};

/**
 * 获取权限名称
 * @param {string} permissionType - 权限类型
 * @returns {string} 权限名称
 */
const getPermissionName = (permissionType) => {
  const permissionNames = {
    [PERMISSION_TYPE.USERINFO]: '用户信息',
    [PERMISSION_TYPE.USERPROFILE]: '用户信息',
    [PERMISSION_TYPE.USERADDRESS]: '通讯地址',
    [PERMISSION_TYPE.USERPHONE]: '手机号码',
    [PERMISSION_TYPE.USERLOCATION]: '位置信息',
    [PERMISSION_TYPE.CAMERA]: '相机',
    [PERMISSION_TYPE.RECORD]: '录音',
    [PERMISSION_TYPE.ALBUM]: '相册',
    [PERMISSION_TYPE.INVOICE]: '发票',
    [PERMISSION_TYPE.INVOICE_TITLE]: '发票抬头',
    [PERMISSION_TYPE.WERUN]: '微信运动',
    [PERMISSION_TYPE.BLUETOOTH]: '蓝牙',
    [PERMISSION_TYPE.CALENDAR]: '日历'
  };
  
  return permissionNames[permissionType] || '未知';
};

module.exports = {
  PERMISSION_TYPE,
  checkPermission,
  requestPermission,
  showPermissionDialog
};

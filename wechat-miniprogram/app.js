App({
  onLaunch: function() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager();
      updateManager.onCheckForUpdate(function(res) {
        if (res.hasUpdate) {
          updateManager.onUpdateReady(function() {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好，是否重启应用？',
              success: function(res) {
                if (res.confirm) {
                  updateManager.applyUpdate();
                }
              }
            });
          });
          updateManager.onUpdateFailed(function() {
            wx.showModal({
              title: '更新提示',
              content: '新版本下载失败，请检查网络后重试'
            });
          });
        }
      });
    }

    this.globalData = {
      userInfo: null,
      chatList: [],
      hasUserInfo: false,
      canIUse: wx.canIUse('button.open-type.getUserInfo')
    };

    this.checkPermissions();
  },

  checkPermissions: function() {
    wx.getSetting({
      success: (res) => {
        if (!res.authSetting['scope.userLocation']) {
          console.log('Location permission not granted');
        }
        if (!res.authSetting['scope.writePhotosAlbum']) {
          console.log('Photo album permission not granted');
        }
      }
    });
  },

  onError: function(err) {
    console.error('App error:', err);
  }
});

Page({
  data: {
    userInfo: {},
    hasUserInfo: false,
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
    chatList: [
      {
        id: 1,
        avatar: '/images/avatar1.png',
        name: '张三',
        lastMessage: '你好，最近怎么样？',
        time: '10:30',
        unread: 2
      },
      {
        id: 2,
        avatar: '/images/avatar2.png',
        name: '李四',
        lastMessage: '我发了一张图片给你',
        time: '昨天',
        unread: 0,
        isImage: true
      },
      {
        id: 3,
        avatar: '/images/avatar3.png',
        name: '王五',
        lastMessage: '我分享了一个位置给你',
        time: '星期一',
        unread: 1,
        isLocation: true
      }
    ]
  },

  onLoad: function() {
    if (wx.getUserProfile) {
      this.setData({
        canIUseGetUserProfile: true
      });
    }
    
    this.generateMockData();
  },

  generateMockData: function() {
    const mockData = this.data.chatList;
    const names = ['Alex', 'Blake', 'Casey', 'Dana', 'Ellis', 'Francis', 'Glen', 'Harper'];
    const messages = [
      '你好，最近怎么样？',
      '周末有空吗？',
      '我发了一张图片给你',
      '我分享了一个位置给你',
      '明天见！',
      '好的，没问题',
      '谢谢你的帮助',
      '收到了，稍后回复'
    ];
    
    for (let i = 4; i <= 50; i++) {
      const nameIndex = Math.floor(Math.random() * names.length);
      const messageIndex = Math.floor(Math.random() * messages.length);
      const isImage = Math.random() > 0.8;
      const isLocation = !isImage && Math.random() > 0.8;
      
      mockData.push({
        id: i,
        avatar: `/images/avatar${(i % 5) + 1}.png`,
        name: names[nameIndex] + i,
        lastMessage: messages[messageIndex],
        time: this.getRandomTime(),
        unread: Math.floor(Math.random() * 5),
        isImage: isImage,
        isLocation: isLocation
      });
    }
    
    this.setData({
      chatList: mockData
    });
  },
  
  getRandomTime: function() {
    const times = ['刚刚', '10:30', '昨天', '星期一', '星期二', '上周'];
    return times[Math.floor(Math.random() * times.length)];
  },

  navigateToChat: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/chat/chat?id=' + id
    });
  },

  getUserProfile: function(e) {
    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (res) => {
        this.setData({
          userInfo: res.userInfo,
          hasUserInfo: true
        });
      }
    });
  }
});

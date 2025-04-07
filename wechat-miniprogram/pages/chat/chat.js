Page({
  data: {
    chatId: null,
    chatInfo: {},
    messages: [],
    inputValue: '',
    isLoading: false,
    showImagePicker: false,
    showLocationPicker: false
  },

  onLoad: function(options) {
    const chatId = options.id;
    this.setData({
      chatId: chatId
    });
    
    this.loadChatInfo(chatId);
    this.loadMessages(chatId);
  },

  loadChatInfo: function(chatId) {
    const chatInfo = {
      id: chatId,
      name: '聊天对象 ' + chatId,
      avatar: '/images/avatar' + (chatId % 5 + 1) + '.png',
      online: true
    };
    
    this.setData({
      chatInfo: chatInfo
    });
    
    wx.setNavigationBarTitle({
      title: chatInfo.name
    });
  },

  loadMessages: function(chatId) {
    this.setData({
      isLoading: true
    });
    
    setTimeout(() => {
      const messages = this.generateMockMessages(chatId);
      
      this.setData({
        messages: messages,
        isLoading: false
      });
      
      this.scrollToBottom();
    }, 500);
  },

  generateMockMessages: function(chatId) {
    const messages = [];
    const count = 10 + Math.floor(Math.random() * 10);
    
    for (let i = 0; i < count; i++) {
      const isSelf = Math.random() > 0.5;
      const type = this.getRandomMessageType();
      
      let content = '';
      let imageUrl = '';
      let location = null;
      
      if (type === 'text') {
        content = this.getRandomTextMessage();
      } else if (type === 'image') {
        imageUrl = '/images/sample' + (i % 5 + 1) + '.jpg';
      } else if (type === 'location') {
        location = {
          name: '示例位置 ' + i,
          address: '示例地址 ' + i,
          latitude: 39.9 + Math.random() * 0.1,
          longitude: 116.3 + Math.random() * 0.1
        };
      }
      
      messages.push({
        id: i,
        type: type,
        content: content,
        imageUrl: imageUrl,
        location: location,
        isSelf: isSelf,
        time: this.getRandomTime(),
        status: isSelf ? (Math.random() > 0.8 ? 'sending' : 'sent') : ''
      });
    }
    
    return messages;
  },

  getRandomMessageType: function() {
    const types = ['text', 'text', 'text', 'text', 'image', 'location'];
    return types[Math.floor(Math.random() * types.length)];
  },

  getRandomTextMessage: function() {
    const messages = [
      '你好，最近怎么样？',
      '周末有空吗？',
      '好的，没问题',
      '谢谢你的帮助',
      '收到了，稍后回复',
      '这是一条测试消息',
      '明天见！',
      '好久不见，最近在忙什么？',
      '我刚刚看到一个很有趣的事情',
      '你能帮我一个忙吗？'
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  },

  getRandomTime: function() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes() - Math.floor(Math.random() * 30);
    return (hours < 10 ? '0' + hours : hours) + ':' + (minutes < 10 ? '0' + minutes : minutes);
  },

  onInputChange: function(e) {
    this.setData({
      inputValue: e.detail.value
    });
  },

  sendMessage: function() {
    const content = this.data.inputValue.trim();
    if (!content) return;
    
    const newMessage = {
      id: this.data.messages.length,
      type: 'text',
      content: content,
      isSelf: true,
      time: this.getCurrentTime(),
      status: 'sending'
    };
    
    const messages = this.data.messages.concat(newMessage);
    
    this.setData({
      messages: messages,
      inputValue: ''
    });
    
    this.scrollToBottom();
    
    setTimeout(() => {
      const updatedMessages = this.data.messages.map(msg => {
        if (msg.id === newMessage.id) {
          return {
            ...msg,
            status: 'sent'
          };
        }
        return msg;
      });
      
      this.setData({
        messages: updatedMessages
      });
    }, 500);
  },

  getCurrentTime: function() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    return (hours < 10 ? '0' + hours : hours) + ':' + (minutes < 10 ? '0' + minutes : minutes);
  },

  scrollToBottom: function() {
    setTimeout(() => {
      wx.createSelectorQuery()
        .select('#message-list')
        .boundingClientRect(rect => {
          if (rect) {
            wx.pageScrollTo({
              scrollTop: rect.height,
              duration: 300
            });
          }
        })
        .exec();
    }, 100);
  },

  showImagePicker: function() {
    this.setData({
      showImagePicker: true
    });
  },

  hideImagePicker: function() {
    this.setData({
      showImagePicker: false
    });
  },

  onImageSelected: function(e) {
    const imageUrl = e.detail.imageUrl;
    
    const newMessage = {
      id: this.data.messages.length,
      type: 'image',
      imageUrl: imageUrl,
      isSelf: true,
      time: this.getCurrentTime(),
      status: 'sending'
    };
    
    const messages = this.data.messages.concat(newMessage);
    
    this.setData({
      messages: messages,
      showImagePicker: false
    });
    
    this.scrollToBottom();
    
    setTimeout(() => {
      const updatedMessages = this.data.messages.map(msg => {
        if (msg.id === newMessage.id) {
          return {
            ...msg,
            status: 'sent'
          };
        }
        return msg;
      });
      
      this.setData({
        messages: updatedMessages
      });
    }, 800);
  },

  showLocationPicker: function() {
    this.setData({
      showLocationPicker: true
    });
  },

  hideLocationPicker: function() {
    this.setData({
      showLocationPicker: false
    });
  },

  onLocationSelected: function(e) {
    const location = e.detail.location;
    
    const newMessage = {
      id: this.data.messages.length,
      type: 'location',
      location: location,
      isSelf: true,
      time: this.getCurrentTime(),
      status: 'sending'
    };
    
    const messages = this.data.messages.concat(newMessage);
    
    this.setData({
      messages: messages,
      showLocationPicker: false
    });
    
    this.scrollToBottom();
    
    setTimeout(() => {
      const updatedMessages = this.data.messages.map(msg => {
        if (msg.id === newMessage.id) {
          return {
            ...msg,
            status: 'sent'
          };
        }
        return msg;
      });
      
      this.setData({
        messages: updatedMessages
      });
    }, 800);
  },

  chooseImage: function() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFilePaths[0];
        
        const newMessage = {
          id: this.data.messages.length,
          type: 'image',
          imageUrl: tempFilePath,
          isSelf: true,
          time: this.getCurrentTime(),
          status: 'sending'
        };
        
        const messages = this.data.messages.concat(newMessage);
        
        this.setData({
          messages: messages
        });
        
        this.scrollToBottom();
        
        setTimeout(() => {
          const updatedMessages = this.data.messages.map(msg => {
            if (msg.id === newMessage.id) {
              return {
                ...msg,
                status: 'sent'
              };
            }
            return msg;
          });
          
          this.setData({
            messages: updatedMessages
          });
        }, 800);
      }
    });
  },

  chooseLocation: function() {
    wx.chooseLocation({
      success: (res) => {
        const location = {
          name: res.name,
          address: res.address,
          latitude: res.latitude,
          longitude: res.longitude
        };
        
        const newMessage = {
          id: this.data.messages.length,
          type: 'location',
          location: location,
          isSelf: true,
          time: this.getCurrentTime(),
          status: 'sending'
        };
        
        const messages = this.data.messages.concat(newMessage);
        
        this.setData({
          messages: messages
        });
        
        this.scrollToBottom();
        
        setTimeout(() => {
          const updatedMessages = this.data.messages.map(msg => {
            if (msg.id === newMessage.id) {
              return {
                ...msg,
                status: 'sent'
              };
            }
            return msg;
          });
          
          this.setData({
            messages: updatedMessages
          });
        }, 800);
      }
    });
  },

  previewImage: function(e) {
    const url = e.currentTarget.dataset.url;
    wx.previewImage({
      current: url,
      urls: [url]
    });
  },

  viewLocation: function(e) {
    const location = e.currentTarget.dataset.location;
    wx.openLocation({
      latitude: location.latitude,
      longitude: location.longitude,
      name: location.name,
      address: location.address,
      scale: 18
    });
  }
});

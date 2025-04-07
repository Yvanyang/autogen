Component({
  /**
   * Component properties
   */
  properties: {
    count: {
      type: Number,
      value: 9
    },
    sizeType: {
      type: Array,
      value: ['original', 'compressed']
    },
    sourceType: {
      type: Array,
      value: ['album', 'camera']
    },
    maxSize: {
      type: Number,
      value: 10 * 1024 * 1024 // 10MB
    }
  },

  /**
   * Component initial data
   */
  data: {
    files: [],
    showPreview: false,
    currentPreview: '',
    isUploading: false
  },

  /**
   * Component methods
   */
  methods: {
    chooseImage: function() {
      const that = this;
      wx.chooseImage({
        count: this.properties.count,
        sizeType: this.properties.sizeType,
        sourceType: this.properties.sourceType,
        success: (res) => {
          const files = res.tempFiles.filter(file => {
            if (file.size > this.properties.maxSize) {
              wx.showToast({
                title: '图片过大，请选择小于10MB的图片',
                icon: 'none'
              });
              return false;
            }
            return true;
          });
          
          const newFiles = this.data.files.concat(files.map(file => {
            return {
              path: file.path,
              size: file.size
            };
          }));
          
          this.setData({
            files: newFiles
          });
          
          this.triggerEvent('change', { files: newFiles });
        }
      });
    },
    
    deleteImage: function(e) {
      const index = e.currentTarget.dataset.index;
      const files = this.data.files;
      files.splice(index, 1);
      
      this.setData({
        files: files
      });
      
      this.triggerEvent('change', { files: files });
    },
    
    previewImage: function(e) {
      const index = e.currentTarget.dataset.index;
      const files = this.data.files;
      
      wx.previewImage({
        current: files[index].path,
        urls: files.map(file => file.path)
      });
    },
    
    showPreview: function(e) {
      const index = e.currentTarget.dataset.index;
      this.setData({
        showPreview: true,
        currentPreview: this.data.files[index].path
      });
    },
    
    hidePreview: function() {
      this.setData({
        showPreview: false,
        currentPreview: ''
      });
    },
    
    uploadImages: function() {
      if (this.data.files.length === 0) {
        wx.showToast({
          title: '请先选择图片',
          icon: 'none'
        });
        return;
      }
      
      this.setData({
        isUploading: true
      });
      
      setTimeout(() => {
        this.setData({
          isUploading: false
        });
        
        this.triggerEvent('upload', { 
          files: this.data.files,
          success: true
        });
      }, 1000);
    },
    
    selectAndUpload: function() {
      wx.chooseImage({
        count: 1,
        sizeType: this.properties.sizeType,
        sourceType: this.properties.sourceType,
        success: (res) => {
          const file = res.tempFiles[0];
          if (file.size > this.properties.maxSize) {
            wx.showToast({
              title: '图片过大，请选择小于10MB的图片',
              icon: 'none'
            });
            return;
          }
          
          this.triggerEvent('select', { 
            imageUrl: file.path,
            size: file.size
          });
        }
      });
    }
  }
});

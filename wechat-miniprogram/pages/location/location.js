Page({
  data: {
    latitude: 39.908823,
    longitude: 116.397470,
    markers: [],
    scale: 14,
    searchValue: '',
    searchResults: [],
    isSearching: false,
    selectedLocation: null,
    showSearchResults: false
  },

  onLoad: function(options) {
    this.getCurrentLocation();
  },

  getCurrentLocation: function() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        const latitude = res.latitude;
        const longitude = res.longitude;
        
        this.setData({
          latitude: latitude,
          longitude: longitude,
          markers: [{
            id: 0,
            latitude: latitude,
            longitude: longitude,
            width: 32,
            height: 32,
            callout: {
              content: '当前位置',
              color: '#000000',
              fontSize: 14,
              borderRadius: 3,
              borderWidth: 1,
              borderColor: '#cccccc',
              bgColor: '#ffffff',
              padding: 5,
              display: 'ALWAYS',
              textAlign: 'center'
            }
          }]
        });
        
        this.getAddressFromLocation(latitude, longitude);
      },
      fail: (err) => {
        console.error('Failed to get location:', err);
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        });
      }
    });
  },

  getAddressFromLocation: function(latitude, longitude) {
    setTimeout(() => {
      const address = {
        name: '当前位置',
        address: '北京市朝阳区某某街道',
        latitude: latitude,
        longitude: longitude
      };
      
      this.setData({
        selectedLocation: address
      });
    }, 500);
  },

  onRegionChange: function(e) {
    if (e.type === 'end' && e.causedBy === 'drag') {
      const mapContext = wx.createMapContext('locationMap');
      mapContext.getCenterLocation({
        success: (res) => {
          const latitude = res.latitude;
          const longitude = res.longitude;
          
          this.setData({
            markers: [{
              id: 0,
              latitude: latitude,
              longitude: longitude,
              width: 32,
              height: 32,
              callout: {
                content: '所选位置',
                color: '#000000',
                fontSize: 14,
                borderRadius: 3,
                borderWidth: 1,
                borderColor: '#cccccc',
                bgColor: '#ffffff',
                padding: 5,
                display: 'ALWAYS',
                textAlign: 'center'
              }
            }]
          });
          
          this.getAddressFromLocation(latitude, longitude);
        }
      });
    }
  },

  onSearchInput: function(e) {
    const value = e.detail.value;
    this.setData({
      searchValue: value
    });
    
    if (value.length > 0) {
      this.searchLocation(value);
    } else {
      this.setData({
        searchResults: [],
        showSearchResults: false
      });
    }
  },

  searchLocation: function(keyword) {
    this.setData({
      isSearching: true,
      showSearchResults: true
    });
    
    setTimeout(() => {
      const results = this.getMockSearchResults(keyword);
      
      this.setData({
        searchResults: results,
        isSearching: false
      });
    }, 500);
  },

  getMockSearchResults: function(keyword) {
    const results = [
      {
        id: 1,
        name: keyword + ' 广场',
        address: '北京市朝阳区' + keyword + '广场',
        latitude: 39.908823 + Math.random() * 0.02 - 0.01,
        longitude: 116.397470 + Math.random() * 0.02 - 0.01
      },
      {
        id: 2,
        name: keyword + ' 大厦',
        address: '北京市海淀区' + keyword + '大厦',
        latitude: 39.908823 + Math.random() * 0.02 - 0.01,
        longitude: 116.397470 + Math.random() * 0.02 - 0.01
      },
      {
        id: 3,
        name: keyword + ' 公园',
        address: '北京市东城区' + keyword + '公园',
        latitude: 39.908823 + Math.random() * 0.02 - 0.01,
        longitude: 116.397470 + Math.random() * 0.02 - 0.01
      }
    ];
    
    return results;
  },

  selectLocation: function(e) {
    const index = e.currentTarget.dataset.index;
    const location = this.data.searchResults[index];
    
    this.setData({
      latitude: location.latitude,
      longitude: location.longitude,
      markers: [{
        id: 0,
        latitude: location.latitude,
        longitude: location.longitude,
        width: 32,
        height: 32,
        callout: {
          content: location.name,
          color: '#000000',
          fontSize: 14,
          borderRadius: 3,
          borderWidth: 1,
          borderColor: '#cccccc',
          bgColor: '#ffffff',
          padding: 5,
          display: 'ALWAYS',
          textAlign: 'center'
        }
      }],
      selectedLocation: location,
      showSearchResults: false,
      searchValue: location.name
    });
  },

  clearSearch: function() {
    this.setData({
      searchValue: '',
      searchResults: [],
      showSearchResults: false
    });
  },

  confirmLocation: function() {
    if (!this.data.selectedLocation) {
      wx.showToast({
        title: '请先选择位置',
        icon: 'none'
      });
      return;
    }
    
    const pages = getCurrentPages();
    const prevPage = pages[pages.length - 2];
    
    if (prevPage && prevPage.onLocationSelected) {
      prevPage.onLocationSelected({
        detail: {
          location: this.data.selectedLocation
        }
      });
    }
    
    wx.navigateBack();
  },

  cancelSelection: function() {
    wx.navigateBack();
  }
});

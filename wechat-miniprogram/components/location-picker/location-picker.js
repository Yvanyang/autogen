Component({
  /**
   * Component properties
   */
  properties: {
    latitude: {
      type: Number,
      value: 39.908823
    },
    longitude: {
      type: Number,
      value: 116.397470
    },
    scale: {
      type: Number,
      value: 14
    },
    showLocation: {
      type: Boolean,
      value: true
    },
    markers: {
      type: Array,
      value: []
    }
  },

  /**
   * Component initial data
   */
  data: {
    searchValue: '',
    searchResults: [],
    isSearching: false,
    selectedLocation: null
  },

  /**
   * Component lifecycle
   */
  lifetimes: {
    attached: function() {
      this.mapContext = wx.createMapContext('map', this);
      
      if (!this.properties.latitude || !this.properties.longitude) {
        this.getCurrentLocation();
      } else {
        this.updateMarker(this.properties.latitude, this.properties.longitude);
      }
    }
  },

  /**
   * Component methods
   */
  methods: {
    getCurrentLocation: function() {
      wx.getLocation({
        type: 'gcj02',
        success: (res) => {
          const latitude = res.latitude;
          const longitude = res.longitude;
          
          this.setData({
            latitude: latitude,
            longitude: longitude
          });
          
          this.updateMarker(latitude, longitude);
          
          this.triggerEvent('locationchange', {
            latitude: latitude,
            longitude: longitude
          });
        },
        fail: (err) => {
          console.error('Failed to get location:', err);
          wx.showToast({
            title: '获取位置失败，请检查位置权限',
            icon: 'none'
          });
        }
      });
    },
    
    updateMarker: function(latitude, longitude) {
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
    },
    
    onMapTap: function(e) {
      const latitude = e.detail.latitude;
      const longitude = e.detail.longitude;
      
      this.updateMarker(latitude, longitude);
      
      this.getLocationInfo(latitude, longitude);
      
      this.triggerEvent('locationchange', {
        latitude: latitude,
        longitude: longitude
      });
    },
    
    onRegionChange: function(e) {
      if (e.type === 'end' && e.causedBy === 'drag') {
        this.mapContext.getCenterLocation({
          success: (res) => {
            const latitude = res.latitude;
            const longitude = res.longitude;
            
            this.updateMarker(latitude, longitude);
            
            this.getLocationInfo(latitude, longitude);
            
            this.triggerEvent('locationchange', {
              latitude: latitude,
              longitude: longitude
            });
          }
        });
      }
    },
    
    getLocationInfo: function(latitude, longitude) {
      if (wx.canIUse('chooseLocation')) {
        this.setData({
          selectedLocation: {
            latitude: latitude,
            longitude: longitude,
            name: '所选位置',
            address: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
          }
        });
        
        this.triggerEvent('locationselect', {
          location: this.data.selectedLocation
        });
      }
    },
    
    onSearchInput: function(e) {
      const value = e.detail.value;
      this.setData({
        searchValue: value
      });
    },
    
    searchLocation: function() {
      const keyword = this.data.searchValue.trim();
      if (!keyword) return;
      
      this.setData({
        isSearching: true
      });
      
      if (wx.canIUse('chooseLocation')) {
        wx.chooseLocation({
          success: (res) => {
            const location = {
              name: res.name,
              address: res.address,
              latitude: res.latitude,
              longitude: res.longitude
            };
            
            this.setData({
              latitude: location.latitude,
              longitude: location.longitude,
              selectedLocation: location,
              isSearching: false
            });
            
            this.updateMarker(location.latitude, location.longitude);
            
            this.triggerEvent('locationselect', {
              location: location
            });
          },
          fail: () => {
            this.setData({
              isSearching: false
            });
          }
        });
      } else {
        wx.showToast({
          title: '该设备不支持位置搜索',
          icon: 'none'
        });
        
        this.setData({
          isSearching: false
        });
      }
    },
    
    selectLocation: function(e) {
      const index = e.currentTarget.dataset.index;
      const location = this.data.searchResults[index];
      
      this.setData({
        latitude: location.latitude,
        longitude: location.longitude,
        selectedLocation: location
      });
      
      this.updateMarker(location.latitude, location.longitude);
      
      this.triggerEvent('locationselect', {
        location: location
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
      
      this.triggerEvent('confirm', {
        location: this.data.selectedLocation
      });
    },
    
    cancelSelection: function() {
      this.triggerEvent('cancel');
    }
  }
});

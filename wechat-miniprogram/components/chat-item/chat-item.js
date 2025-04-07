Component({
  /**
   * Component properties
   */
  properties: {
    item: {
      type: Object,
      value: {}
    },
    customStyle: {
      type: String,
      value: ''
    }
  },

  /**
   * Component initial data
   */
  data: {
    defaultAvatar: '/images/default-avatar.png'
  },

  /**
   * Component methods
   */
  methods: {
    onTap: function() {
      this.triggerEvent('tap', { id: this.properties.item.id });
    },
    
    onLongPress: function() {
      this.triggerEvent('longpress', { id: this.properties.item.id });
    },
    
    onAvatarTap: function(e) {
      e.stopPropagation();
      this.triggerEvent('avatartap', { id: this.properties.item.id });
    }
  }
});

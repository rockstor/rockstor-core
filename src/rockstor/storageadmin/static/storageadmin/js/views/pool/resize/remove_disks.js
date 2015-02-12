PoolRemoveDisks = RockstorWizardPage.extend({
  
  initialize: function() {
    this.disks = new DiskCollection();
    this.template = window.JST.pool_resize_remove_disks;
    this.disks_template = window.JST.common_disks_table;
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
    this.disks.on('reset', this.renderDisks, this);
  },

  render: function() {
    RockstorWizardPage.prototype.render.apply(this, arguments);
    this.disks.fetch();
    return this;
  },

  renderDisks: function() {
    var disks = this.disks.filter(function(disk) {
      return disk.get('pool_name') == this.model.get('pool').get('name');
    }, this);
    this.$('#ph-disks-table').html(this.disks_template({disks: disks}));
  },

  save: function() {
    var _this = this;
    var checked = this.$(".diskname:checked").length;
    var diskNames = [];
    this.$(".diskname:checked").each(function(i) {
      diskNames.push($(this).val());
    });
    return $.ajax({
      url: '/api/pools/' + this.model.get('pool').get('name')+'/remove',
      type: 'PUT',
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({
        'disks': diskNames, 
        'raid_level': this.model.get('pool').get('raid')
      }),
      success: function() { },
      error: function(request, status, error) {
      }
    });
  }

});


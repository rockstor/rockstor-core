PoolAddDisks = RockstorWizardPage.extend({

  initialize: function() {
    this.disks = new DiskCollection();
    this.template = window.JST.pool_resize_add_disks;
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
    var disks = this.disks.reject(function(disk) {
      return disk.get('pool_name') == this.model.get('pool').get('name');
    }, this);
    this.$('#ph-disks-table').html(this.disks_template({disks: disks}));
  },
});



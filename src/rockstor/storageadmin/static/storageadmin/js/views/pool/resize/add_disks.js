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
    var disks = this.disks.filter(function(disk) {
      return disk.available();
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
    this.model.set('diskNames', diskNames);
    if (this.model.get('raidChange')) {
      this.model.set('raidLevel', this.$('#raid-level').val());
    }
    return $.Deferred().resolve();
  }
});



PoolRaidChange = RockstorWizardPage.extend({

  initialize: function() {
    this.disks = new DiskCollection();
    this.template = window.JST.pool_resize_raid_change;
    this.disks_template = window.JST.common_disks_table;
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
    this.disks.on('reset', this.renderDisks, this);
  },
  
  render: function() {
    $(this.el).html(this.template({pool: this.model.get('pool')}));
    this.disks.fetch();
    return this;
  },
  
  renderDisks: function() {
    var _this = this;
    var disks = this.disks.filter(function(disk) {
      return disk.available();
    }, this);
    this.$('#ph-disks-table').html(this.disks_template({disks: disks}));
    this.$('#raid-change-form').validate({
      rules: {
        'raid-level': {
          required: true
        },
        'disknamehidden': {
          required: function(el) {
            console.log('in disknamehidden required');
            console.log(_this.$(".diskname:checked").length);
            return _this.$(".diskname:checked").length > 0;
          }
        }
      },
      messages: {
        'disknamehidden': 'Please select at least one disk'
      }
    });
  },
  
  save: function() {
    var valid = $('#raid-change-form').valid();
    console.log(valid);
    if (valid) {
      var raidLevel = this.$('#raid-level').val();
      var checked = this.$(".diskname:checked").length;
      var diskNames = [];
      this.$(".diskname:checked").each(function(i) {
        diskNames.push($(this).val());
      });
      this.model.set('raidLevel', raidLevel);
      this.model.set('diskNames', diskNames);
      return $.Deferred().resolve();
    } else {
      return $.Deferred().reject();
    }
  }

});

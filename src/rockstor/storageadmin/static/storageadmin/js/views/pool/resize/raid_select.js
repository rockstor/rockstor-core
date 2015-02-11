PoolRaidSelect = RockstorWizardPage.extend({

  initialize: function() {
    this.template = window.JST.pool_resize_raid_select;
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
  },
  
  render: function() {
    $(this.el).html(this.template({pool: this.model.get('pool')}));
    return this;
  },
  
  save: function() {
    var raid = this.$('#raid-level').val();
    if (!_.isEmpty(raid)) {
      this.model.set('raidLevel', this.$('#raid-level').val());
    } else {
      this.model.set('raidLevel', this.model.get('pool').get('raid'));
    }
    return $.Deferred().resolve();
  }

});

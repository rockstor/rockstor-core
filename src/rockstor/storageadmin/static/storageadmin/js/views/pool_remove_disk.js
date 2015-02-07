PoolRemoveDisk = RockstorWizardPage.extend({
  initialize: function() {
    this.template = window.JST.pool_resize_remove_disks;
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
  },
});


PoolResizeChoice = RockstorWizardPage.extend({

  initialize: function() {
    this.template = window.JST.pool_resize_choice;
    console.log('PoolResizeChoice - template is ');
    console.log(this.template);
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
  },

  events: {
    'click #add-disks': 'addDisks',
    'click #remove-disks': 'removeDisks',
  },

  addDisks: function() {
    this.model.set('resize-choice', 'add');
    this.evAgg.trigger('nextPage');
  },

  removeDisks: function() {
    this.model.set('resize-choice', 'remove');
    this.parent.nextPage();
  },

});

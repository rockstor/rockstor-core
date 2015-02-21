PoolResizeSummary = RockstorWizardPage.extend({

  initialize: function() {
    this.template = window.JST.pool_resize_summary;
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
  },

  save: function() {
    var _this = this;
    var choice = this.model.get('choice');
    var raidLevel = null;
    if (choice == 'add') {
      raidLevel = this.model.get('raidChange') ?  this.model.get('raidLevel') :
        this.model.get('pool').get('raid');
      return $.ajax({
        url: '/api/pools/' + this.model.get('pool').get('name')+'/add',
        type: 'PUT',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          'disks': this.model.get('diskNames'), 
          'raid_level': raidLevel
        }),
      });
    } else if (choice == 'remove') {
      return $.ajax({
        url: '/api/pools/' + this.model.get('pool').get('name')+'/remove',
        type: 'PUT',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          'disks': this.model.get('diskNames'), 
          'raid_level': this.model.get('pool').get('raid')
        }),
        success: function() { },
        error: function(request, status, error) {
        }
      });
    } else if (choice == 'raid') {
      return $.ajax({
        url: '/api/pools/' + this.model.get('pool').get('name')+'/add',
        type: 'PUT',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          'disks': this.model.get('diskNames'), 
          'raid_level': this.model.get('raidLevel')
        }),
        success: function() { },
        error: function(request, status, error) {
        }
      });
    }
  }
});




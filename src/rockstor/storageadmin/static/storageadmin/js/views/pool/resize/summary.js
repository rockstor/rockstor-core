PoolResizeSummary = RockstorWizardPage.extend({

  initialize: function() {
    this.template = window.JST.pool_resize_summary;
    var choice = this.model.get('choice');
    var raidLevel = null;
    var poolDisks = _.map(this.model.get('pool').get('disks'), function(disk) {
      return disk.name;
    })
    if (choice == 'add') {
      this.newRaidLevel = this.model.get('raidChange') ?  this.model.get('raidLevel') :
        this.model.get('pool').get('raid');
      this.newDisks = _.union(poolDisks, this.model.get('diskNames'));
    } else if (choice == 'remove') {
      this.newRaidLevel = this.model.get('pool').get('raid');
      this.newDisks = _.difference(poolDisks, this.model.get('diskNames'));
    } else if (choice == 'raid') {
      this.newRaidLevel = this.model.get('raidLevel');
      this.newDisks = _.union(poolDisks, this.model.get('diskNames'));
    }
    RockstorWizardPage.prototype.initialize.apply(this, arguments);
  },
  
  render: function() {
    $(this.el).html(this.template({
      model: this.model,
      newRaidLevel: this.newRaidLevel,
      newDisks: this.newDisks
    }));
    return this;
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




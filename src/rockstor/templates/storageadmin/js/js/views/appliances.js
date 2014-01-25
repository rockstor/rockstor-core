/*
 *
 * @licstart  The following is the entire license notice for the 
 * JavaScript code in this page.
 * 
 * Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
 * This file is part of RockStor.
 * 
 * RockStor is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 * 
 * RockStor is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 * 
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 * 
 */

AppliancesView = RockstoreLayoutView.extend({
  
  events: {
    'click .delete-appliance': 'deleteAppliance',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.appliances = new ApplianceCollection();
    this.template = window.JST.appliances_appliances;
    this.new_appliance_template = window.JST.common_new_appliance;
    this.dependencies.push(this.appliances); 
  },

  render: function() {
    console.log('in appliances.js render');
    this.fetch(this.renderApplianceList, this)
    return this;
  },
  
  renderApplianceList: function() {
    $(this.el).html(this.template({appliances: this.appliances}));
    this.appliances.on('reset', this.renderApplianceList, this);
  },

  newAppliance: function() {
    console.log('add clicked');
    this.$('#new-appliance-container').html(this.new_appliance_template());
  },

  addAppliance: function(event) {
    event.preventDefault();
    var _this = this;
    console.log('submitting form');
    var new_appliance = new Appliance();
    new_appliance.save(
      {
        ip: this.$('#ip').val(),
        username: this.$('#username').val(),
        password: this.$('#password').val(),
        current_appliance: false
      },
      { 
        success: function(model, response, options) {
          console.log('new appliance added successfully');
          _this.$('#new-appliance-container').empty();
          _this.appliances.fetch();
        },
        error: function(model, xhr, options) {
          var msg = xhr.responseText;
          try {
            msg = JSON.parse(msg).detail;
          } catch(err) {
          }
          _this.$('#add-appliance-msg').html(msg);
        }
      }
    );

  },

  deleteAppliance: function(event) {
    event.preventDefault();
    var _this = this;
    var tgt = $(event.currentTarget);
    var appliance = new Appliance();
    appliance.set({
      ip: tgt.attr('id'),
      id: tgt.attr('data-id')
    });
    console.log(appliance);
    appliance.destroy({
      success: function(model, response, options) {
        console.log('appliance deleted successfully');
        _this.appliances.fetch();

      },
      error: function(model, xhr, options) {
        var msg = xhr.responseText;
        console.log('error while deleting appliance');
      }

    });
  }
});


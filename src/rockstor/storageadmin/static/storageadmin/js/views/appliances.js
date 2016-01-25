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

AppliancesView = RockstorLayoutView.extend({

  events: {
    'click .delete-appliance': 'deleteAppliance',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.collection = new ApplianceCollection();
    this.template = window.JST.appliances_appliances;
    this.new_appliance_template = window.JST.common_new_appliance;
    this.dependencies.push(this.collection);
    this.collection.on('reset', this.renderApplianceList, this);
    this.initHandlebarHelpers();
  },

  render: function() {
    this.fetch(this.renderApplianceList, this)
    return this;
  },

  renderApplianceList: function() {
    $(this.el).html(this.template({collection: this.collection}));
  },

  newAppliance: function() {
    this.$('#new-appliance-container').html(this.new_appliance_template());
  },

  deleteAppliance: function(event) {
    var _this = this;
    event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    var appliance = new Appliance();
    appliance.set({
      ip: button.attr('id'),
      id: button.attr('data-id')
    });
    if(confirm("Delete appliance:  " + appliance.get('ip') + " ...Are you sure?")){
      disableButton(button);
      appliance.destroy({
        success: function(model, response, options) {
          enableButton(button);
          _this.collection.fetch();
        },
        error: function(model, xhr, options) {
          enableButton(button);
          var msg = xhr.responseText;
        }
      });
    }
  },

  initHandlebarHelpers: function(){
    Handlebars.registerHelper('print_appliances_tbody', function() {
      var html = '';
       this.collection.each(function(appliance) {
          var mgmt_port = appliance.get('mgmt_port'),
              applianceID = appliance.get('id'),
              applianceIP = appliance.get('ip'),
              hostName = appliance.get('hostname'),
              currAppliance = appliance.get('current_appliance');
          html += '<tr>';
          html += '<td>' + appliance.get("uuid") + '</td>';
          html += '<td>';
          html += '<i class="fa fa-desktop"></i>&nbsp';
          if (currAppliance) {
              html += applianceIP + ' <span class="required">*</span>';
          } else {
              html += '<a href="https://' + applianceIP + ':' + mgmt_port + '" target="_blank">' + applianceIP + '</a>';
          }
          html += '</td>';
          html += '<td>' + hostName + ' <a href="#edit-hostname/'+ applianceID +'/edit" title="Edit Hostname"><i class="glyphicon glyphicon-pencil"></i></a></td>';
          html += '<td>' + mgmt_port + '</td>';
          html += '<td>';
            if (!currAppliance) {
              html += '<a class="delete-appliance" id="' + applianceIP + '" data-id="' + applianceId + '" href="#"><i class="glyphicon glyphicon-trash"></i></a>';
            } else {
              html += 'N/A';
            }
          html += '</td>';
        html += '</tr>';
      });
        return new Handlebars.SafeString(html);
    });
  }
});

// Add pagination
Cocktail.mixin(AppliancesView, PaginationMixin);

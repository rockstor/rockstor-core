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
    this.collection = new ApplianceCollection();
    this.template = window.JST.appliances_appliances;
    this.pagination_template = window.JST.common_pagination;
    this.new_appliance_template = window.JST.common_new_appliance;
    this.dependencies.push(this.collection); 
    this.collection.on('reset', this.renderApplianceList, this);
  },

  render: function() {
    this.fetch(this.renderApplianceList, this)
    return this;
  },
  
  renderApplianceList: function() {
    $(this.el).html(this.template({collection: this.collection}));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
  },

  newAppliance: function() {
    this.$('#new-appliance-container').html(this.new_appliance_template());
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
    appliance.destroy({
      success: function(model, response, options) {
        _this.appliances.fetch();

      },
      error: function(model, xhr, options) {
        var msg = xhr.responseText;
      }

    });
  }
});

// Add pagination
Cocktail.mixin(AppliancesView, PaginationMixin);


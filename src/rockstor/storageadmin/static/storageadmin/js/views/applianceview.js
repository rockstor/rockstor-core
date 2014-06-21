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

ApplianceView = RockstorLayoutView.extend({
  
  events: {
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.diskcollection = new DiskCollection();
    this.template = window.JST.appliances_appliance_view;
    this.dependencies.push(this.diskcollection); 

    this.cpucollection = new DiskCollection();
    this.dependencies.push(this.cpucollection);
    this.cordscollection = new DiskCollection();
    this.dependencies.push(this.cordscollection);
    this.memorycollection = new DiskCollection();
    this.dependencies.push(this.memorycollection);

    this.diskcollection.on('reset', this.renderApplianceView, this);
  },

  render: function() {
    this.fetch(this.renderApplianceView, this)
    return this;
  },

  renderApplianceView: function() {
    $(this.el).html(this.template({collection: this.diskcollection, cpucollection: this.cpucollection,
    	cordscollection: this.cordscollection, memorycollection: this.memorycollection}));
  }

});

// Add pagination
Cocktail.mixin(AppliancesView, PaginationMixin);


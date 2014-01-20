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

SetupDisksView = Backbone.View.extend({
  tagName: 'div',
  
  events: {
    'click #rescan': 'rescan',
  },

  initialize: function() {
    this.template = window.JST.setup_disks;
    this.disks_table_template = window.JST.setup_disks_table;
    this.paginationTemplate = window.JST.common_pagination;
    this.collection = new DiskCollection();
    this.collection.on('reset', this.renderDisks, this);
  },

  render: function() {
    $(this.el).html(this.template());
    this.rescan();
    return this;
  },

  renderDisks: function() {
    this.$('#disks-table').html(this.disks_table_template({disks: this.collection}));
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
  },

  rescan: function() {
    var _this = this;
    $.ajax({
      url: "/api/disks/scan",
      type: "POST"
    }).done(function() {
      _this.collection.fetch();
    });
  },

});

// Add pagination
Cocktail.mixin(SetupDisksView, PaginationMixin);


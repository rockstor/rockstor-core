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

DisksView = Backbone.View.extend({
  events: {
    "click #setup": "setupDisks"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.disk_disks;
    this.disks_table_template = window.JST.disk_disks_table;
    this.pagination_template = window.JST.common_pagination;
    this.collection = new DiskCollection; 
    this.collection.on("reset", this.renderDisks, this);
  },

  render: function() {
    this.collection.fetch();
    return this;
  },
  
  renderDisks: function() {
    $(this.el).html(this.template({ collection: this.collection }));
    this.$("#disks-table-ph").html(this.disks_table_template({
      collection: this.collection
    }));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
  },

  setupDisks: function() {
    var _this = this;
    $.ajax({
      url: "/api/disks/",
      type: "POST"
    }).done(function() {
      // reset the current page
      _this.collection.page = 1;
      _this.collection.fetch();
    });
  },

});

// Add pagination
Cocktail.mixin(DisksView, PaginationMixin);


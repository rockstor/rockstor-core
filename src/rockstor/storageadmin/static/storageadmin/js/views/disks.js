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
    "click #setup": "setupDisks",
    'click .wipe': 'wipeDisk',
    'click .delete': 'deleteDisk'
  },

  initialize: function() {
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
    if (this.$('[rel=tooltip]')) { 
      this.$("[rel=tooltip]").tooltip('hide');
    }
    $(this.el).html(this.template({ collection: this.collection }));
    // remove existing tooltips
    this.$("#disks-table-ph").html(this.disks_table_template({
      collection: this.collection
    }));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
    this.$("#disks-table").tablesorter();
    this.$("[rel=tooltip]").tooltip({ 
      placement: "bottom",
      container: '#disks-table' 
    });
  },

  setupDisks: function() {
    var _this = this;
    $.ajax({
      url: "/api/disks/scan",
      type: "POST"
    }).done(function() {
      // reset the current page
      _this.collection.page = 1;
      _this.collection.fetch();
    });
  },

  wipeDisk: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var diskName = button.data('disk-name');
    if (confirm('Wipe disk ' + diskName + ' ... Are you sure?')) {
      $.ajax({
        url: '/api/disks/' + diskName + '/wipe',
        type: 'POST',
        success: function(data, status, xhr) {
          _this.render();
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });
    }
  },

  deleteDisk: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var diskName = button.data('disk-name');
    if (confirm('Delete disk ' + diskName + ' ... Are you sure?')) {
      $.ajax({
        url: '/api/disks/' + diskName,
        type: 'DELETE',
        success: function(data, status, xhr) {
          _this.render();
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });
    }
  },

});

// Add pagination
Cocktail.mixin(DisksView, PaginationMixin);


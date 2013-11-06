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

/*
 * Pools View
 */

PoolsView = RockstoreLayoutView.extend({
  events: {
    "click a[data-action=delete]": "deletePool"
  },

  initialize: function() {
	
	this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.pool_pools;
    this.pools_table_template = window.JST.pool_pools_table;
    this.pagination_template = window.JST.common_pagination;
    this.collection = new PoolCollection();
    this.disks = new DiskCollection();
    this.dependencies.push(this.disks);
    this.dependencies.push(this.collection);
    this.collection.on("reset", this.renderPools, this);
    
  },

  render: function() {
    this.fetch(this.renderPools,this);
    return this;
  },

  renderPools: function() {
    var _this = this;
    $(this.el).html(this.template({ collection: this.collection, disks: this.disks }));
    this.$("#pools-table-ph").html(this.pools_table_template({
      collection: this.collection
    }));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
    this.$("#pools-table").tablesorter();
   
    return this;
  },

  deletePool: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    name = button.attr('data-name');
    if(confirm("Delete pool: " + name + " ... Are you sure?")){
      disableButton(button);	
      $.ajax({
        url: "/api/pools/" + name,
        type: "DELETE",
        dataType: "json",
        data: { "name": name },
        success: function() {
          _this.collection.fetch({reset: true});
          enableButton(button);
        },
        error: function(xhr, status, error) {
          var msg = parseXhrError(xhr)
          _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
          enableButton(button);
        }
      });
    }
  }
});

// Add pagination
Cocktail.mixin(PoolsView, PaginationMixin);

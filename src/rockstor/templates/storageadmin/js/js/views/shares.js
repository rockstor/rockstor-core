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
 * Shares View
 */

SharesView = RockstoreLayoutView.extend({
  events: {
    "click button[data-action=delete]": "deleteShare"
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    
    this.template = window.JST.share_shares;
    this.shares_table_template = window.JST.share_shares_table;
    this.pagination_template = window.JST.common_pagination;
    
    this.pools = new PoolCollection();
    this.collection = new ShareCollection();
    this.dependencies.push(this.pools);
    this.dependencies.push(this.collection);
    
    this.pools.on("reset", this.renderShares, this);
    this.collection.on("reset", this.renderShares, this);
  },

  render: function() {
    this.fetch(this.renderShares, this);
    return this;
  },

  renderShares: function() {
    if (!this.pools.fetched || !this.collection.fetched) { 
      return false;
    }
    $(this.el).html(this.template({
      collection: this.collection,
      pools: this.pools
    }));
    this.$("#shares-table-ph").html(this.shares_table_template({
      collection: this.collection,
      pools: this.pools
    }));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
    this.$("#shares-table").tablesorter();
  },

  deleteShare: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    name = button.attr('data-name');
    if(confirm("Delete share:  " + name + " ...Are you sure?")){
      $.ajax({
        url: "/api/shares/"+name,
        type: "DELETE",
        dataType: "json",
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
Cocktail.mixin(SharesView, PaginationMixin);


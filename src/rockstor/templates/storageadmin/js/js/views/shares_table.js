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
 * Shares Table View
 */

SharesTableView = RockstoreModuleView.extend({
  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.pools = this.options.pools;
  },

  render: function() {
    this.template = window.JST.share_shares_table_template;
    $(this.el).empty();
    $(this.el).append(this.template({shares: this.collection, pools: this.pools}));
    this.$('#shares-table').tablesorter();
    var _this = this;
    this.$('button[data-action=delete]').click(function(event) {
      name = $(event.target).attr('data-name');
      pool = $(event.target).attr('data-pool');
      size = $(event.target).attr('data-size');
      console.log('sending delete event');
      $.ajax({
        url: "/api/shares/"+name+"/",
        type: "DELETE",
        dataType: "json",
        data: { "pool": pool, "size": size }
      }).done(function() {
        console.log('delete successful');
        _this.collection.fetch();
      });
    });
    return this;
  }
});

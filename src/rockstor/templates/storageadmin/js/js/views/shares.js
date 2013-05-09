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

SharesLayoutView = RockstoreLayoutView.extend({
  tagName: 'div',
  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.share_shares_template;
    // create collection
    this.pools = new PoolCollection();
    this.shares = new ShareCollection();
    // set dependencies
    this.dependencies.push(this.pools);
    this.dependencies.push(this.shares);
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;
  },

  renderSubViews: function() {
    $(this.el).append(this.template({
      shares: this.shares,
      pools: this.pools
    }));
    // Create subviews
    this.subviews['shares-table'] = new SharesTableView({
      collection: this.shares,
      pools: this.pools
    });
    // Bind subviews to models
    this.shares.on('reset', this.subviews['shares-table'].render, this.subviews['shares-table']);
    // render subviews
    this.$('#ph-shares-table').append(this.subviews['shares-table'].render().el);
  }

});


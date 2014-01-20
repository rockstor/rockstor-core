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
 * Support View
 */

SupportView = RockstoreLayoutView.extend({
  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.support_support_template;
    
    // create collection
    this.support = new SupportCaseCollection();
    // add dependencies
    this.dependencies.push(this.support);
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;
  },

  renderSubViews: function() {
    // create subviews
    this.subviews['support-table'] = new SupportTableView({collection: this.support});
    // bind subviews to collection
    this.support.on('reset', this.subviews['support-table'].render, this.subviews['support-table']);
    // render
    $(this.el).empty();
    $(this.el).append(this.template());
    // render subviews
    this.$('#ph-support-table').append(this.subviews['support-table'].render().el);
  },

  attachActions: function() {
    
  }

});


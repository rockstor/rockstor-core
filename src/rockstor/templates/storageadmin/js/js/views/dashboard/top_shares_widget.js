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


TopSharesWidget = RockStorWidgetView.extend({

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_sample;
    this.displayName = this.options.displayName;
  },

  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName
    }));
    return this;
  },

});
RockStorWidgets.available_widgets.push({ 
    name: 'top_shares', 
    displayName: 'Top Shares by usage', 
    view: 'TopSharesWidget',
    description: 'Displays Top Shares by percentage of space used',
    defaultWidget: true,
    rows: 1,
    cols: 1,
    category: 'Storage', 
    position: 3
});


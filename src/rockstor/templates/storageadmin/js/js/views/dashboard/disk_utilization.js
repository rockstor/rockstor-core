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


DiskUtilizationWidget = RockStorWidgetView.extend({

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_disk_utilization;
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
      maximized: this.maximized
    }));
  },

  render: function() {
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    return this;
  },

  getData: function(context, t1, t2) {
    var _this = context;
    $.ajax({
      url: "/api/sm/sprobes/diskstat/?limit=10", 
      type: "GET",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.update(data.results);
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }
    });

  },

  cleanup: function() {
    if (!_.isNull(this.intervalId)) {
      window.clearInterval(this.intervalId);
    }
  },

});

RockStorWidgets.widgetDefs.push({ 
    name: 'disk_utilization', 
    displayName: 'Disk Usage', 
    view: 'DiskUtilizationWidget',
    description: 'Display disk utilization',
    defaultWidget: false,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
});



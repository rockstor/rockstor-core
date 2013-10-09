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
    var _this = this;
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_top_shares;
    this.shares = new ShareCollection();
    this.shares.pageSize = 1000;
    this.colors = ["#F25805"];
    this.graphOptions = { 
      grid : { 
        hoverable : true,
        borderWidth: {
          top: 1,
          right: 1,
          bottom: 1,
          left: 1
        },
        aboveData: true,
        borderColor: "#ddd",
        color: "#aaa"
      },
			series: {
        bars: { show: true, barWidth: 0.5, fillColor: this.colors[0], align: 'center' },
        shadowSize: 0	// Drawing is faster without shadows
			},
      tooltip: true,
      tooltipOpts: {
        content: '%y.2KB'
      }
    };
    this.graphWidth = this.maximized ? 400 : 200;
    this.$('#top-shares-graph-ph').css('width', this.graphWidth);
  },

  render: function() {
    var _this = this;
    // call render of base
    this.constructor.__super__.render.apply(this, arguments);
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName,
      maximized: this.maximized
    }));
    this.shares.fetch({
      success: function(collection, response, options) {
        _this.renderTopShares();
      }
    }) 
    return this;
  },
 
  renderTopShares: function() {
    this.shareData = _.sortBy(this.shares.models, function(s) {
      return s.get('usage');
    });

    this.graphOptions.yaxis = {
      min: 0,
      max: _.max(this.shareData, function(d) { 
        return d.get('usage'); 
      }).get('usage'),
      tickFormatter: this.shareUsageTickFormatter,
    };
    this.graphOptions.xaxis = {
      ticks: 5,
      tickFormatter: this.shareNameTickFormatter(this.shareData)
    };

    var rawData = [];
    _.each(this.shareData, function(d,i) {
      rawData.push([i, d.get('usage')]);
    });
    if (rawData.length < 5) {
      for (var i=rawData.length; i<5; i++) {
        rawData.push([i, null]);
      }
    } else {
      rawData = rawData.slice(0,5);
    }
    var series = {label: 'Usage', data: rawData, color: this.colors[0]};
    $.plot(this.$('#top-shares-graph-ph'), [series], this.graphOptions);

  },

  shareNameTickFormatter: function(shareData) {
    return function(val, axis) {
      if (!_.isUndefined(shareData[val])) {
        return shareData[val].get('name');
      } else {
        return '';
      }
    }
  },

  shareUsageTickFormatter: function(val, axis) {
    return humanize.filesize(val*1024);
  },

  resize: function(event) {
    this.constructor.__super__.resize.apply(this, arguments);
    this.graphWidth = this.maximized ? 400 : 200;
    this.$('#top-shares-graph-ph').css('width', this.graphWidth);
  }

});

RockStorWidgets.widgetDefs.push({ 
    name: 'top_shares', 
    displayName: 'Top Shares by Usage', 
    view: 'TopSharesWidget',
    description: 'Display top shares by usage',
    defaultWidget: false,
    rows: 1,
    cols: 5,
    maxRows: 2,
    maxCols: 10,
    category: 'Storage', 
});




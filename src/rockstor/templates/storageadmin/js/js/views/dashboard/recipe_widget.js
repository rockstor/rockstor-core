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

RecipeWidget = RockStorWidgetView.extend({

  events: {
    'click .start-recipe' : 'start',
    'click .stop-recipe' : 'stop',
    'click .resize-widget': 'resize',
    'click .close-widget': 'close',

  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_recipe;
    this.displayName = this.options.displayName;
    this.timestamp = 0;
    // periodically check status while polling for data is 
    // going on. this interval controls the frequence
    this.scInterval = 0; 
    //this.nfsData = [[[1,10],[2,10], [3,10], [4,10], [5,10], [6,10],
      //[7,10], [8,10], [9,10], [10,10]]];
    this.nfsData = [0,0,0,0,0,0,0,0,0,0];

		this.graphOptions = {
			lines: { show: true },
			points: { show: true },
			xaxis: {
        min: 0,
        max: 10,
				tickDecimals: 0,
				tickSize: 1
			},
      yaxis: {
        min: 0,
        max: 100
      }
		};
    
  },

  render: function() {
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName
    }));
    var series = [[]];
    for (i=0; i<10; i++) {
      series[0].push([i, this.nfsData[i]]);
    }
    //$.plot(this.$('#nfsgraph'), this.makeSeries(this.nfsData), this.graphOptions);
    return this;
  },

  start: function(event) {
    var _this = this;
    if (!_.isUndefined(event)) {
      event.preventDefault();
    }
    $.ajax({
      url: '/api/recipes/nfs/start',
      type: 'POST',
      data: {},
      dataType: "json",
      success: function(data, textStatus, jqXHR) {
        logger.debug('started recipe');
        _this.$('#recipestatus').html('Recipe started - getting status');
        _this.waitTillRunning(data.recipe_uri);
      },
      error: function(jqXHR, textStatus, error) {
        logger.debug(error);
      }
    });

  },

  waitTillRunning: function(recipe_uri) {
    var _this = this;
    logger.debug('polling till running');
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        $.ajax({
          url: recipe_uri + '?status',
          type: 'GET',
          dataType: "json",
          success: function(data, textStatus, jqXHR) {
            if (data.recipe_status == 'running') {
              _this.$('#recipestatus').html('Recipe running - getting data');
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // TODO show message - "recipe started, polling for data"
              // start polling for Data
              logger.debug('recipe running');
              _this.pollForData(recipe_uri);
            } else {

            }
          },
          error: function(jqXHR, textStatus, error) {
            window.clearInterval(_this.statusIntervalId);
            logger.debug(error);
            // TODO show error message on widget
          }
        });
      }
    }(), 5000)

  },

  pollForData: function(recipe_uri) {
    var _this = this;
    logger.debug('starting polling for data');
    this.dataIntervalId = window.setInterval(function() {
      return function() { 
        $.ajax({
          url: recipe_uri + '?t=' + this.timestamp,
          type: 'GET',
          success: function(data, textStatus, jqXHR) {
            _this.$('#recipestatus').html('Recipe running ');
            logger.debug('received data ');
            logger.debug(data);
            
            _this.nfsData = _this.nfsData.slice(1);
            _this.nfsData.push(data.value);
            $.plot('#nfsgraph', _this.makeSeries(_this.nfsData), _this.graphOptions);
            // TODO update timestamp from data
            // _this.timestamp = new timestamp from data
          },
          error: function(jqXHR, textStatus, error) {
            window.clearInterval(_this.dataIntervalId);
            logger.debug(error);
            // TODO show error message on widget
          }
        });
      
      
      }
    }(), 2000)

  },

  stop: function(event) {
    if (!_.isUndefined(event)) {
      event.preventDefault();
    }
    if (!_.isUndefined(this.dataIntervalId) && !_.isNull(this.dataIntervalId)) {
      window.clearInterval(this.dataIntervalId);
      this.$('#recipestatus').html('Recipe stopped ');
    }

  },

  makeSeries: function(data) {
    var series = [[]];
    for (i=0; i<10; i++) {
      series[0].push([i,data[i]]);
    }
    return series;
  }

});

RockStorWidgets.available_widgets.push({ 
  name: 'nfs_recipe', 
  displayName: 'NFS Usage', 
  view: 'RecipeWidget',
  description: 'NFS Usage',
  defaultWidget: false,
  rows: 1,
  cols: 1,
  category: 'Storage'
});


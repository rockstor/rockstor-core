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

  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.dashboard_widgets_recipe;
    this.displayName = this.options.displayName;
    this.timestamp = 0;
    // periodically check status while polling for data is 
    // going on. this interval controls the frequence
    this.sc_interval = 0; 
  },

  render: function() {
    this.constructor.__super__.render.apply(this, arguments);
    var _this = this;
    $(this.el).html(this.template({ 
      module_name: this.module_name,
      displayName: this.displayName
    }));
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
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // TODO show message - "recipe started, polling for data"
              // start polling for Data
              logger.debug('recipe running');
              _this.pollForData(recipe_uri);
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
            logger.debug('received data ');
            logger.debug(data);
            // TODO render new data  
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
    }(), 5000)

  },

  stop: function(event) {
    if (!_.isUndefined(event)) {
      event.preventDefault();
    }

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


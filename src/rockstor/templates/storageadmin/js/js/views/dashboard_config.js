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

DashboardConfigView = Backbone.View.extend({
  events: {
    'click #save': 'save'
  },

  initialize: function() {
    this.available_widgets = this.options.available_widgets;
    this.dashboardconfig = this.options.dashboardconfig;
    this.template = window.JST.dashboard_dashboard_config;
    this.parentView = this.options.parentView;
  },

  render: function() {
    $(this.el).html(this.template({
      available_widgets: this.available_widgets,
      selected_widgets: this.dashboardconfig.get('widgets').split(',')
    }));
    return this;
  },

  save: function(event) {
    event.preventDefault();
    logger.debug('in dashboard_config save');
    var _this = this;
    var selected_widgets = this.dashboardconfig.get('widgets').split(',');
    this.$("input.widget-name").each(function() {
      var name = $(this).val();
      n = _.indexOf(selected_widgets, name);
      if (this.checked && n == -1 ) {
        selected_widgets.push(name);
      } else if (!this.checked && n != -1) {
        selected_widgets.splice(n,1);
      }
    });
    this.dashboardconfig.set({'widgets': selected_widgets.join(',')});
    logger.debug(selected_widgets);
    this.dashboardconfig.save( null, {
      success: function(model, response, options) {
        logger.debug('saved dashboardconfig successfully');
        _this.parentView.$('#dashboard-config-popup').modal('hide');
        _this.parentView.renderWidgets();
      },
      error: function(model, xhr, options) {
        logger.debug('error while saving dashboardconfig');
        _this.parentView.$('#dashboard-config-popup').modal('hide');
        var msg = xhr.responseText;
        try {
          msg = JSON.parse(msg).detail;
        } catch(err) {
        }
        logger.debug(msg);
      }

    });
  }

});



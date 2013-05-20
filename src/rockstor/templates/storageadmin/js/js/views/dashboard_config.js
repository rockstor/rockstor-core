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
    this.dashboardconfig = this.options.dashboardconfig;
    this.template = window.JST.dashboard_dashboard_config;
    this.parentView = this.options.parentView;
  },

  render: function() {
    $(this.el).html(this.template({
      wSelected: this.dashboardconfig.getConfig()
    }));
    return this;
  },

  save: function(event) {
    event.preventDefault();
    logger.debug('in dashboard_config save');
    var _this = this;
    var wSelected = this.dashboardconfig.getConfig();
    
    this.parentView.widgetsContainer.trigger('ss-destroy');  
    this.$("input.widget-name").each(function() {
      var name = $(this).val();
      var isPresent = _.some(wSelected, function(w) {
        return w.name == name;
      });
      if (this.checked && !isPresent ) {
        _this.parentView.addWidget(
          RockStorWidgets.findByName(name),
          _this.parentView.widgetsContainer,
          _this.parentView.cleanupArray
        )
      } else if (!this.checked && isPresent) {
        _this.parentView.removeWidget(name);
      }
    });
    this.parentView.$('#dashboard-config-popup').modal('hide');
    this.parentView.widgetsContainer.shapeshift();
    this.parentView.saveWidgetConfiguration();
    
  }

});



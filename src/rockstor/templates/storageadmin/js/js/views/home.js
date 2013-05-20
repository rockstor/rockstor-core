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
 * View for the homepage/dashboard
 */

var HomeLayoutView = RockstoreLayoutView.extend({
  events: {
    'click #configure-dashboard': 'dashboardConfig',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.home_home_template;
    // create models and collections
    this.sysinfo = new SysInfo();
    this.appliances = new ApplianceCollection();
    this.dashboardconfig = new DashboardConfig();
    // add dependencies
    this.dependencies.push(this.sysinfo);
    this.dependencies.push(this.appliances);
    this.dependencies.push(this.dashboardconfig);

    /*
    this.available_widgets = { 
      'sysinfo': { display_name: 'System Information', view: 'SysInfoWidget' },
      'cpu_usage': { display_name: 'CPU Usage', view: 'CpuUsageWidget' },
      'sample': { display_name: 'Sample Widget', view: 'SampleWidget' },
      'alerts': { display_name: 'Alerts', view: 'SampleWidget' },
      'top_shares_usage': { display_name: 'Top Shares By Usage', view: 'SampleWidget' },
    };
    */
    this.cleanupArray = []; // widgets add themselves here so that their cleanup routines can be called from this view's cleanup
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;
  },

  renderSubViews: function() {

    // redirect to setup if current appliance is not setup
    var current_appliance = undefined;
    if (this.appliances.length > 0) {
      var current_appliance = this.appliances.find(function(appliance) {
        return appliance.get('current_appliance') == true; 
      })
    }
    if (_.isUndefined(current_appliance)) {
      app_router.navigate('setup', {trigger: true});
      return;
    }
    // set current appliance name
    $('#appliance-name').html(current_appliance.get('ip')); 

    // render template
    $(this.el).empty();
    $(this.el).append(this.template());
    this.widgetsContainer = this.$('.widgets-container');
    // render dashboard widgets
    this.renderWidgets();

  },

  dashboardConfig: function() {
    var dashboardConfigPopup = this.$('#dashboard-config-popup').modal({
      show: false
    });
    this.$('#dashboard-config-content').empty();
    this.$('#dashboard-config-content').append((new DashboardConfigView({
      parentView: this,
      available_widgets: this.available_widgets,
      dashboardconfig: this.dashboardconfig
    })).render().el);
    this.$('#dashboard-config-popup').modal('show');

  },

  renderWidgets: function() {

    var _this = this;
    this.widgetsContainer.empty();
    
    var wConfigs = null;
    wConfigs = this.dashboardconfig.getConfig();
    if (_.isNull(wConfigs)) {
      this.dashboardconfig.setConfig(RockStorWidgets.defaultWidgets());
      wConfigs = this.dashboardconfig.getConfig();
      logger.debug('dashboardconfig was null, set it to');
      logger.debug(wConfigs);
    }
    this.cleanupArray.length = 0;
    // Add widgets to ul (widgetsContainer);
    _.each(wConfigs, function(wConfig, index, list ) {
      _this.addWidget(wConfig, _this.widgetsContainer, _this.cleanupArray);
    });
    // call shapeshift to do layout
    this.widgetsContainer.shapeshift();
   
    // set handlers for layout modification events
    this.widgetsContainer.on('ss-arranged', function(e, selected) {
      logger.debug('in arranged handler');
    });
    this.widgetsContainer.on('ss-drop-complete', function(e, selected) {
      logger.debug('in drop-complete handler');
      _this.saveWidgetConfiguration();
    });
    this.widgetsContainer.on('ss-trashed', function(e, selected) {
      logger.debug('in ss-trashed handler');
    });

  },

  addWidget: function(widgetConf, container, cleanupArray) {
    var li = null;
    var viewName = widgetConf.view;
    if (!_.isUndefined(window[viewName] && !_.isNull(window[viewName]))) {
      var view = new window[viewName]({
        displayName: widgetConf.displayName,
        name: widgetConf.name,
        cleanupArray: this.cleanupArray,
      });
      // create li for widget
      li = $("<li>");
      li.attr("data-ss-colspan", widgetConf.cols);
      li.attr("data-ss-rowspan", widgetConf.rows);
      container.append(li);
      var position_div = $('<div class="position"></div>');
      li.append(position_div);
      position_div.append(view.render().el);
      cleanupArray.push(view);
    }
  },

  saveWidgetConfiguration: function() {
    var lis = this.widgetsContainer.find('li');
    var tmp = [];
    lis.each(function(index) {
      var li = $(this);
      var name = li.find('div.widget').attr('id').replace('_widget','');; 
      var widgetConf = RockStorWidgets.findByName(name);
      var rows = li.attr('data-ss-rowspan');
      var cols = li.attr('data-ss-colspan');
      logger.debug('widget name = ' + name + '   position = ' + index + 
      '  rows = ' + rows + '  cols = ' + cols);
      tmp.push({
        name: name, 
        displayName: widgetConf.displayName,
        view: widgetConf.view,
        rows: rows, 
        cols: cols,
        position: index, 
      });
    });
    this.dashboardconfig.set({ widgets: JSON.stringify(tmp) });
    this.dashboardconfig.save( null, {
      success: function(model, response, options) {
        logger.debug('saved dashboardconfig successfully');
      },
      error: function(model, xhr, options) {
        logger.debug('error while saving dashboardconfig');
        var msg = xhr.responseText;
        try {
          msg = JSON.parse(msg).detail;
        } catch(err) {
        }
        logger.debug(msg);
      }
    });
  },

  cleanup: function() {
    _.each(this.cleanupArray, function(widget) {
      if (_.isFunction(widget.cleanup)) {
        widget.cleanup();
      }
    });
  }

});


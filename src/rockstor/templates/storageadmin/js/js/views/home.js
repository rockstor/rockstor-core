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

    this.available_widgets = { 
      'sysinfo': { display_name: 'System Information', view: 'SysInfoWidget' },
      'cpu_usage': { display_name: 'CPU Usage', view: 'CpuUsageWidget' },
      'sample': { display_name: 'Sample Widget', view: 'SampleWidget' },
      'alerts': { display_name: 'Alerts', view: 'SampleWidget' },
      'top_shares_usage': { display_name: 'Top Shares By Usage', view: 'SampleWidget' },
    };
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

    // render dashboard widgets
    this.renderWidgets();

    //create subviews
    //this.subviews['sysinfo'] = new SysInfoModule({model: this.sysinfo});
    //this.subviews['cpuusage'] = new CpuUsageModule();
    // render subviews
    //this.$('#ph-sysinfo').append(this.subviews['sysinfo'].render().el);
    //this.$('#ph-cpuusage').append(this.subviews['cpuusage'].render().el);
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
    parentElem = this.$('#widgets-container');
    var _this = this;
    parentElem.empty();
    logger.debug('in home.js renderWidgets');
    // if no dashboardconfig for this user exists, add sysinfo
    // and cpu_usage widgets to selected
    if (_.isUndefined(this.dashboardconfig.get('widgets'))) {
      this.dashboardconfig.set('widgets', "sysinfo,cpu_usage");
    }
    var i = 0;
    logger.debug('widgets are');
    logger.debug(this.dashboardconfig.get('widgets'));
    widget_list = this.dashboardconfig.get('widgets').split(',');
    logger.debug(widget_list);
    this.cleanupArray.length = 0;
    _.each(widget_list, function(widget, index, list ) {
      logger.debug('rendering ' + widget); 
      logger.debug('i = ' + i);
      if ((i % 3) == 0) {
        logger.debug('creating row');
        row = $('<div class="row-fluid"/>');
        parentElem.append(row);
      }
      var view_name = _this.available_widgets[widget].view;
      if (!_.isUndefined(window[view_name] && !_.isNull(window[view_name]))) {
        logger.debug('creating view ' + view_name);
        var view = new window[view_name]({
          display_name: _this.available_widgets[widget].display_name,
          cleanupArray: _this.cleanupArray
        });
        _this.cleanupArray.push(view);
        var span = $('<div class="span4"></div>');
        span.append(view.render().el);
        row.append(span);
        i = i+1;
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


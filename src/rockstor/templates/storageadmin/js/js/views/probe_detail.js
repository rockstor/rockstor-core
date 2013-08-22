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

/* Services */

ProbeDetailView = RockstoreLayoutView.extend({
  events: {
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.probeId = this.options.probeId;
    this.probeName = this.options.probeName;
    this.probeRunTmp = Backbone.Model.extend({
      url: function() {
        return "/api/sm/sprobes/metadata" + "/" + this.id + "?format=json";
      },
      parse: function(response, options) {
        return response[0];
      }
    });
    this.probeRun = new this.probeRunTmp({
      id: this.probeId,
      name: this.probeName,
    });
    this.dependencies.push(this.probeRun);
    this.template = window.JST.probes_probe_detail;
    // The class to append for the display status for each possible probe
    // status. null indicates not to display that status
    // Initialized -> running -> done - means append 'done' to the display 
    // status for the 'Initialized' state if probe status is running.
    this.probeStatusMap = {
      Initialized: {
        created: "done", running: "done", stopped: "done", error: "done"
      },
      Running: {
        created: "todo", running: "done", stopped: "done", error: null
      },
      Completed: {
        created: "todo", running: "todo", stopped: "done", error: null
      },
      Error: {
        created: null, running: null, stopped: null, error: "error"
      }
    };
    this.probeStates = {
      STOPPED: 'stopped', CREATED: 'created',
      RUNNING: 'running', ERROR: 'error',
    };
    this.statusPollInterval = 2; // poll interval for status changes 
  },

  render: function() {
   this.fetch(this.renderProbeDetail, this);
   return this;
  },

  renderProbeDetail: function() {
    var _this = this;
    $(this.el).append(this.template({
      probeRun: this.probeRun,
      runStatus: this.probeRun.get("state"),
      statusMap: this.probeStatusMap
    }));

    var tmp = _.find(RockStorProbeMap, function(p) {
      return p.name == _this.probeRun.get('name');
    });
    if (tmp) {
      var viewName = tmp.view;
      this.probeClass = window[viewName];
      console.log("found probe class " + this.probeClass);
    } else {
      console.log("did not find probe view for probe " + this.probeRun.get("name"));
    }
    this.probeRun.trigger(this.probeRun.get("state"));
  },

  probeInitialized: function() {
    // TODO update probe status bar
    
    // TODO display waiting for probe to run message in viz area
    
    // poll till Running
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        _this.probeRun.fetch({
          success: function(model, response, options) {
            if (_this.probeRun.get('state') == _this.probeStates.RUNNING) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to running state
              _this.probeRun.trigger(_this.probeEvents.RUNNING);
            } else if (_this.probeRun.get('state') == _this.probeStates.ERROR) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to error state
              _this.probeRun.trigger(_this.probeEvents.ERROR);
            }
          },
          error: function(model, response, options) {
            // stop polling for status
            window.clearInterval(_this.statusIntervalId);
            // go to error state
            _this.probeRun.trigger(_this.probeEvents.ERROR);
          }
        });
      }
    }(), this.statusPollInterval)
  },

  probeRunning: function() {
    if (probeClass) {
      //var probeVizView = new NfsShareClientDistribView({probe: this.probeRun});
      //this.probeVizView = new window[viewName]({probe: this.probeRun});
      //this.$("#probe-viz").empty();
      //this.$("#probe-viz").append(probeVizView.render().el);
    } else {
      console.log("No probe Class found for probe " + this.probeRun.get("name"));
    }
  },

  probeStopped: function() {
    if (this.probeVizView) {
      this.probeVizView.trigger(this.probeEvents.STOPPED);
    } else {
      if (probeClass) {
        //this.probeVizView = new window[viewName]({probe: this.probeRun});
        //this.$("#probe-viz").empty();
        //this.$("#probe-viz").append(probeVizView.render().el);
      } else {
        console.log("No probe Class found for probe " + this.probeRun.get("name"));
      }
    }
  },

  probeError: function() {
    // TODO update probe status bar
    console.log("Probe error!");

    // TODO display error message in viz area
  },

  setProbeEvents: function(probe) {
    probe.on(this.probeStates.CREATED, this.probeInitialized, this);
    probe.on(this.probeStates.RUNNING, this.probeRunning, this);
    probe.on(this.probeStates.STOPPED, this.probeStopped, this);
    probe.on(this.probeStates.ERROR, this.probeError, this);
  },

});




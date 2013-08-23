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
    "click #stop-probe": "stopProbe"
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
    this.time_template = window.JST.probes_probe_time;
    this.action_template = window.JST.probes_probe_actions;
    this.status_template = window.JST.probes_probe_status;
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
    this.statusPollInterval = 2000; // poll interval for status changes 
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
    this.setProbeEvents();
    this.probeRun.trigger(this.probeRun.get("state"));
  },

  probeInitialized: function() {
    this.updateStatus();
    this.updateActions();
    this.updateTime();
    
    // TODO display waiting for probe to run message in viz area
    
    // poll till Running
    this.pollTillStatus(this.probeStates.RUNNING);

    /*
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        _this.probeRun.fetch({
          success: function(model, response, options) {
            if (_this.probeRun.get('state') == _this.probeStates.RUNNING) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to running state
              _this.probeRun.trigger(_this.probeStates.RUNNING);
            } else if (_this.probeRun.get('state') == _this.probeStates.ERROR) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to error state
              _this.probeRun.trigger(_this.probeStates.ERROR);
            }
          },
          error: function(model, response, options) {
            // stop polling for status
            window.clearInterval(_this.statusIntervalId);
            // go to error state
            _this.probeRun.trigger(_this.probeStates.ERROR);
          }
        });
      }
    }(), this.statusPollInterval)
   */
  },

  probeRunning: function() {
    this.updateStatus();
    this.updateActions();
    this.updateTime();
    if (this.probeClass) {
      console.log("rendering probeclass");
      //var probeVizView = new NfsShareClientDistribView({probe: this.probeRun});
      //this.probeVizView = new window[viewName]({probe: this.probeRun});
      //this.$("#probe-viz").empty();
      //this.$("#probe-viz").append(probeVizView.render().el);
    } else {
      console.log("No probe Class found for probe " + this.probeRun.get("name"));
    }
  },

  probeStopped: function() {
    this.updateStatus();
    this.updateActions();
    this.updateTime();
    if (this.probeVizView) {
      this.probeVizView.trigger(this.probeStates.STOPPED);
    } else {
      if (this.probeClass) {
        // TODO initialize probeVizView 
        
        //this.probeVizView = new window[viewName]({probe: this.probeRun});
        //this.$("#probe-viz").empty();
        //this.$("#probe-viz").append(probeVizView.render().el);
      } else {
        console.log("No probe Class found for probe " + this.probeRun.get("name"));
      }
    }
  },

  probeError: function() {
    this.updateStatus();
    this.updateActions();
    this.updateTime();
    console.log("Probe error!");

    // TODO display error message in viz area
  },

  setProbeEvents: function(probe) {
    this.probeRun.on(this.probeStates.CREATED, this.probeInitialized, this);
    this.probeRun.on(this.probeStates.RUNNING, this.probeRunning, this);
    this.probeRun.on(this.probeStates.STOPPED, this.probeStopped, this);
    this.probeRun.on(this.probeStates.ERROR, this.probeError, this);
  },
  
  stopProbe: function(event) {
    if (event) {
      event.preventDefault();
    }
    var button = this.$('#stop-probe');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var _this = this;
    var probeId = this.probeRun.id;
    var probeName = this.probeRun.get("name");
    $.ajax({
      url: "/api/sm/sprobes/" + probeName + "/" + probeId + "/stop?format=json",
      type: 'POST',
      data: {},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        _this.pollTillStatus(_this.probeStates.STOPPED);
      },
      error: function(jqXHR, textStatus, error) {
        var msg = parseXhrError(jqXHR)
        console.log(msg);
      }
    });
  },

  pollTillStopped: function() {
    var _this = this;
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        _this.probeRun.fetch({
          success: function(model, response, options) {
            if (_this.probeRun.get('state') == _this.probeStates.STOPPED) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to running state
              _this.probeRun.trigger(_this.probeStates.STOPPED);
            } else if (_this.probeRun.get('state') == _this.probeStates.ERROR) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to error state
              _this.probeRun.trigger(_this.probeStates.ERROR);
            }
          },
          error: function(model, response, options) {
            // stop polling for status
            window.clearInterval(_this.statusIntervalId);
            // go to error state
            _this.probeRun.trigger(_this.probeStates.ERROR);
          }
        });
      }
    }(), this.statusPollInterval)
  },

  updateActions: function() {
    this.$(".probe-actions").html(this.action_template({
      probeRun: this.probeRun
    }));
  },

  updateStatus: function() {
    this.$(".probe-status").html(this.status_template({
      probeRun: this.probeRun,
      runStatus: this.probeRun.get("state"),
      statusMap: this.probeStatusMap
    }));
  },

  updateTime: function() {
    this.$(".probe-time").html(this.time_template({
      probeRun: this.probeRun,
    }));
  },

  pollTillStatus: function(status) {
    var _this = this;
    this.statusIntervalId = window.setInterval(function() {
      return function() { 
        _this.probeRun.fetch({
          success: function(model, response, options) {
            if (_this.probeRun.get('state') == status) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to running state
              _this.probeRun.trigger(status);
            } else if (_this.probeRun.get('state') == _this.probeStates.ERROR) {
              // stop polling for status
              window.clearInterval(_this.statusIntervalId);
              // go to error state
              _this.probeRun.trigger(_this.probeStates.ERROR);
            }
          },
          error: function(model, response, options) {
            // stop polling for status
            window.clearInterval(_this.statusIntervalId);
            // go to error state
            _this.probeRun.trigger(_this.probeStates.ERROR);
          }
        });
      }
    }(), this.statusPollInterval);
  },

  cleanup: function() {
    // TODO remove any setIntervals
    if (this.probeVizView) {
      this.probeVizView.cleanup();
    }
  }

});




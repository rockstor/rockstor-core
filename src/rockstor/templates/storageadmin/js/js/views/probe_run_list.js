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

ProbeRunListView = RockstoreLayoutView.extend({
  events: {
    "click #cancel-new-probe": "cancelNewProbe",
    "click .stop-probe": "stopProbe",
    "click .view-probe": "viewProbe",
    "click .download-probe-data": "downloadProbeData",

  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.probes_probe_run_list;
    this.paginationTemplate = window.JST.common_pagination;
    this.tableTemplate = window.JST.probes_probe_table;
    this.collection = new ProbeRunCollection();
    this.probeTemplates = new ProbeTemplateCollection();
    this.dependencies.push(this.collection);
    this.dependencies.push(this.probeTemplates);
    this.statusPollInterval = 2000; // poll interval for status changes 
    this.statusIntervalIds = {};
    this.collection.on('reset', this.renderProbeList, this);
  },

  render: function() {
   this.fetch(this.renderProbeList, this);
   return this;
  },

  renderProbeList: function() {
    // get probe template names - TODO fix when the api returns 
    // proper objects
    var probeTemplateNames = this.probeTemplates.map(function(pt) {
      return (_.keys(pt.attributes))[0];
    });
    var _this = this;
    $(this.el).html(this.template({
      probeRuns: this.collection,
      probeTemplates: this.probeTemplates

    }));
    this.renderTable();
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$("[rel=tooltip]").tooltip({ placement: "bottom"});
  },
  
  renderTable: function() {
    this.$("[rel=tooltip]").tooltip("hide");
    this.$("#probe-run-list").html(this.tableTemplate({
      probeRuns: this.collection
    }));
    this.$("#probe-run-table").tablesorter();
  },

  cancelNewProbe: function(event) {
    if (event) {
      event.preventDefault();
    }
    this.$('#new-probe-form').overlay().close();
  },

  stopProbe: function(event) {
    if (event) {
      event.preventDefault();
    }
    var _this = this;
    var probeId = $(event.currentTarget).attr("data-probe-id");
    var probeName = $(event.currentTarget).attr("data-probe-name");
    if (buttonDisabled($(event.currentTarget))) return false;
    disableButton($(event.currentTarget));
    $.ajax({
      url: "/api/sm/sprobes/" + probeName + "/" + probeId + "/stop?format=json",
      type: 'POST',
      data: {},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        var probeRunTmp = Backbone.Model.extend({
          url: function() {
            return "/api/sm/sprobes/metadata" + "/" + probeId + "?format=json";
          },
        });
        var probeRun = new probeRunTmp({ id: probeId, name: probeName });
        _this.pollTillStatus(probeRun, "stopped");
      },
      error: function(jqXHR, textStatus, error) {
        var msg = parseXhrError(jqXHR)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
        console.log(msg);
      }
    });
  },

  viewProbe: function(event) {
    if (event) { event.preventDefault(); }
    var _this = this;
    var probeId = $(event.currentTarget).attr("data-probe-id");
    var probeName = $(event.currentTarget).attr("data-probe-name");
    this.$("[rel=tooltip]").tooltip("hide");
    app_router.navigate("#probeDetail/" + probeName + "/" + probeId, {trigger: true});

  },

  pollTillStatus: function(probeRun, status, callback, errCallback) {
    var _this = this;
    this.statusIntervalIds[probeRun.id] = window.setInterval(function() {
      probeRun.fetch({
        success: function(model, response, options) {
          if (probeRun.get("state") == status ||
              probeRun.get("state") == "error") {
            // stop polling for status
            window.clearInterval(_this.statusIntervalIds[probeRun.id]);
            _this.collection.fetch({
              silent: true,
              success: function(collection, response, options) {
                _this.renderTable();
              },
              error: function(collection, response, options) {
                console.log("error while fetching probe runs");
              }
            });
          } 
        },
        error: function(model, response, options) {
          // stop polling for status
          window.clearInterval(_this.statusIntervalIds[probeRun.id]);
          // go to running state
          _this.renderTable();
        }
      });
    }, this.statusPollInterval);
  },
  
  downloadProbeData: function(event) {
    if (event) { event.preventDefault(); }
    var _this = this;
    var probeId = $(event.currentTarget).attr("data-probe-id");
    var probeName = $(event.currentTarget).attr("data-probe-name");
    document.location.href = this.collection.get(probeId).downloadUrl();
  },

});


// Add pagination
Cocktail.mixin(ProbeRunListView, PaginationMixin);


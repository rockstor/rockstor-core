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
    "click #create-probe": "createProbe",
    "click .stop-probe": "stopProbe"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.probes_probe_run_list;
    this.probeRuns = new ProbeRunCollection();
    this.probeTemplates = new ProbeTemplateCollection();
    this.dependencies.push(this.probeRuns);
    this.dependencies.push(this.probeTemplates);
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
    console.log("probeTemplateNames");
    console.log(probeTemplateNames);
    var _this = this;
    $(this.el).append(this.template({
      probeRuns: this.probeRuns,
      probeTemplateNames: probeTemplateNames

    }));
    this.$("#probe-run-table").tablesorter();
    this.$("#new-probe-form").overlay({
      left: "center",
      load: false
    });
    this.$("#new-probe-button").click(function() {
      _this.$("#new-probe-form").overlay().load();
      
    });
    this.$("[rel=tooltip]").tooltip({ placement: "bottom"});
  },

  createProbe: function(event) {
    if (event) {
      event.preventDefault();
    }
    var _this = this;
    console.log("Creating probe " + this.$("#probe-type").val());
    var probeName = this.$("#probe-type").val();
    $.ajax({
      url: "/api/sm/sprobes/" + probeName + "/" + "?format=json",
      type: 'POST',
      data: {},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        console.log("probe started successfully");
        _this.$("#new-probe-form").overlay().close();
      },
      error: function(jqXHR, textStatus, error) {
        var msg = parseXhrError(xhr)
        console.log(msg);
      }
    });
  },

  cancelNewProbe: function() {
    this.$('#new-probe-form').overlay().close();
  },

  stopProbe: function(event) {
    if (event) {
      event.preventDefault();
    }
    var probeId = $(event.currentTarget).attr("data-probe-id");
    var probeName = $(event.currentTarget).attr("data-probe-name");
    console.log("stopping probe " + probeName + " " + probeId);
    $.ajax({
      url: "/api/sm/sprobes/" + probeName + "/" + probeId + "/stop/?format=json",
      type: 'POST',
      data: {},
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, textStatus, jqXHR) {
        console.log("probe stopped successfully");
      },
      error: function(jqXHR, textStatus, error) {
        var msg = parseXhrError(xhr)
        console.log(msg);
      }
    });
  }


});



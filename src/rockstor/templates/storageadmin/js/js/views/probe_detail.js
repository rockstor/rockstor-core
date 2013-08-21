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
    this.probeStatusMap = {
      Initialized: {
        created: "done",
        running: "done",
        stopped: "done",
        error: "done"
      },
      Running: {
        created: "todo",
        running: "done",
        stopped: "done",
        error: null
      },
      Completed: {
        created: "done",
        running: "todo",
        stopped: "done",
        error: null
      },
      Error: {
        created: "done",
        running: null,
        stopped: null,
        error: "error"
      }
    };
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
  },


});




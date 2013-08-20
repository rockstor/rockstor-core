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
    "click #cancel-new-probe": "cancelNewProbe"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.probes_probe_run_list;
  },

  render: function() {
   this.fetch(this.renderProbeList, this);
   return this;
  },

  renderProbeList: function() {
    var _this = this;
    $(this.el).append(this.template({
    }));
    this.$("#probe-run-table").tablesorter();
    this.$("#new-probe-form").overlay({
      left: "center",
      load: false
    });
    this.$("#new-probe-button").click(function() {
      _this.$('#new-probe-form').overlay().load();
      
    });
    this.$("[rel=tooltip]").tooltip({ placement: "bottom"});
  },

  cancelNewProbe: function() {
    this.$('#new-probe-form').overlay().close();
  }


});



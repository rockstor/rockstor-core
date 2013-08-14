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

SetupNetworkView = Backbone.View.extend({
  tagName: 'div',
  
  initialize: function() {
    this.template = window.JST.setup_network;
    this.interfacesTemplate = window.JST.setup_interfaces;
    this.networkInterfaces = new NetworkInterfaceCollection();
    this.networkInterfaces.on("reset", this.renderInterfaces, this);
    this.networkInterfaces.on("reset", this.setIp, this);
  },

  render: function() {
    $(this.el).html(this.template());
    this.scanNetwork();
    return this;
  },

  scanNetwork: function() {
    var _this = this;
    $.ajax({
      url: "/api/network/", 
      type: "POST",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        console.log("scanned network");
        console.log(data);
        _this.networkInterfaces.fetch();
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }
    });
  },

  renderInterfaces: function() {
    this.$("#interfaces").html(this.interfacesTemplate({
      networkInterfaces: this.networkInterfaces
    }));

  },

  setIp: function() {
    RockStorGlobals.ip = this.networkInterfaces.at(0).get("ipaddr");
    if (_.isNull(RockStorGlobals.ip)) {
      RockStorGlobals.ip = "192.168.1.128";
    }
  }


});



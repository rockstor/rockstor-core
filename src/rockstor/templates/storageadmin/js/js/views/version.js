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

VersionView = RockstoreLayoutView.extend({
  events: {
    'click #update': 'update'
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.update_version_info;
    this.paginationTemplate = window.JST.common_pagination;
  },

  render: function() {
    this.renderVersionInfo();
    return this;
  },

  renderVersionInfo: function() {
    $(this.el).html(this.template());
  },

  update: function() {
    var _this = this;
    $.ajax({
      url: "/api/commands/update", 
      type: "POST",
      dataType: "json",
      global: false, // dont show global loading indicator
      success: function(data, status, xhr) {
        _this.checkIfUp();
      },
      error: function(xhr, status, error) {
        _this.checkIfUp();
      }
    });
  },

  checkIfUp: function() {
    var _this = this;
    this.isUpTimer = window.setInterval(function() {
      $.ajax({
        url: "/api/sm/sprobes/loadavg?limit=1&format=json", 
        type: "GET",
        dataType: "json",
        global: false, // dont show global loading indicator
        success: function(data, status, xhr) {
          window.clearInterval(_this.isUpTimer);
          _this.reloadWindow();
        },
        error: function(xhr, status, error) {
          // server is not up, continue checking
        }
      });
    }, 5000);
  },

  reloadWindow: function() {
    location.reload(true);
  }

});




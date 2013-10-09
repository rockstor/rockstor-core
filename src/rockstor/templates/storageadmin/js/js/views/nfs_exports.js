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

NFSExportsView  = RockstoreModuleView.extend({
  events: {
    'click .delete-nfs-export': 'deleteNfsExport'
  },
    
  initialize: function() {
    this.template = window.JST.nfs_nfs_exports;
    this.module_name = 'nfs_exports';
    this.nfsExportGroups = new NFSExportGroupCollection();
  },

  render: function() {
    var _this = this;
    this.nfsExportGroups.fetch({
      success: function(collection, response, options) {
        $(_this.el).html(_this.template({
          nfsExportGroups: _this.nfsExportGroups,
        }));
      },
      error: function(collection, response, options) {
        console.log(response);
      }
    });
    return this;
  },

  deleteNfsExport: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    disableButton(button)
    var id = $(event.currentTarget).data('id');
    $.ajax({
      url: '/api/nfs-exports/' + id,
      type: 'DELETE',
      dataType: 'json',
      contentType: 'application/json',
      success: function() {
        _this.render();
      },
      error: function(xhr, status, error) {
        enableButton(button);
        var msg = parseXhrError(xhr)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });
  }

});


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

EditNFSExportView = RockstoreLayoutView.extend({
  events: {
      'click #cancel': 'cancel',
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.nfs_edit_nfs_export;
    this.shares = new ShareCollection();
    this.nfsExportGroupId = this.options.nfsExportGroupId;
    this.nfsExportGroup = new NFSExportGroup({id: this.nfsExportGroupId});
    this.dependencies.push(this.nfsExportGroup);
    // dont paginate shares for now
    this.shares.pageSize = 1000; 
    this.dependencies.push(this.shares);
    this.modify_choices = [
      {name: 'ro', value: 'ro'}, 
      {name: 'rw', value: 'rw'},
    ];
    this.sync_choices = [
      {name: 'async', value: 'async'},
      {name: 'sync', value: 'sync'}, 
    ];
  },
  
  render: function() {
    this.fetch(this.renderExportForm, this);
    return this;
  },

  renderExportForm: function() {
    var _this = this;
    $(this.el).html(this.template({
      shares: this.shares,
      nfsExportGroup: this.nfsExportGroup,
      modify_choices: this.modify_choices,
      sync_choices: this.sync_choices
    }));
    $('#edit-nfs-export-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        shares: 'required',  
        host_str: 'required'
      },
      submitHandler: function() {
        var button = $('#update-nfs-export');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
          url: '/api/nfs-exports/' + _this.nfsExportGroup.id,
          type: 'PUT',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(_this.$('#edit-nfs-export-form').getJSON()),
          success: function() {
            app_router.navigate('nfs-exports', {trigger: true});
          },
          error: function(xhr, status, error) {
            enableButton(button);
            var msg = parseXhrError(xhr)
            if (_.isObject(msg)) {
              _this.validator.showErrors(msg);
            } else {
              _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
            }
          }
        });
        return false;
      }
    });
  },
  
  cancel: function(event) {
    event.preventDefault();
    app_router.navigate('nfs-exports', {trigger: true});
  }

});



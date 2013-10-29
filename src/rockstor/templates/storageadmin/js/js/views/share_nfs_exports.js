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

ShareNFSExports  = RockstoreModuleView.extend({
  events: {
    'click #add-export': 'addExport',
    'click #cancel-add-export': 'cancel',
    'click #cancel-edit-export': 'cancel',
    'click .edit-nfs-export': 'editExport',
    'click .delete-nfs-export': 'deleteExport',
  },

  initialize: function() {
    this.template = window.JST.share_nfs_exports;
    this.addTemplate = window.JST.share_add_nfs_export;
    this.editTemplate = window.JST.share_edit_nfs_export;
    this.module_name = 'nfs_exports';
    this.share = this.options.share;
    this.nfsExports = new NFSExportCollection();
    this.nfsExports.setUrl(this.share.get('shareName'));
    this.modify_choices = this.options.modify_choices;
    this.sync_choices = this.options.sync_choices;
    this.appliance_ip = this.options.appliance_ip;
    this.share.on('change', function() {
      this.nfsExports.reset(this.share.get('nfs_exports'));
    }, this)
  },

  render: function() {
    var _this = this;
    this.nfsExports.fetch({
      success: function(collection, response, options) {
        $(_this.el).empty();
        $(_this.el).append(_this.template({
          share: _this.share,
          nfsExports: _this.nfsExports,
          modify_choices: _this.modify_choices,
          sync_choices: _this.sync_choices,
        }));
        if (_this.nfsExports.length > 0) {
          _this.$('#nfs-exports-table-body').append('<tr><td colspan="5">Mount this share using <code>mount ' + _this.appliance_ip + ':' + _this.nfsExports.at(0).get('exports')[0].mount + ' &lt;mount_pt&gt;</code></td></tr>');
        }
      },
      error: function(collection, response, options) {
        logger.debug(response);
      }
    });
    return this;
  },
  
  addExport : function(event) {
    var _this = this;
    event.preventDefault();
    $(this.el).html(this.addTemplate({ 
      share: this.share,
      nfsExports: this.nfsExports,
      modify_choices: this.modify_choices,
      sync_choices: this.sync_choices,
    }));
    this.validator = this.$("#add-nfs-export-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        host_str: "required"
      },
      submitHandler: function() {
        var button = _this.$('#save-export');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
          url: "/api/shares/"+_this.share.get('name')+'/nfs',
          type: "POST",
          dataType: "json",
          data: {
            host_str: _this.$("#host_str").val(),
            mod_choice: _this.$("#mod_choice").val(),  
            sync_choice: _this.$("#sync_choice").val()  
          },
          success: function() {
            enableButton(button);
            _this.render();
          },
          error: function(xhr, status, error) {
            enableButton(button);
            var msg = parseXhrError(xhr)
            if (_.isObject(msg)) {
              _this.validator.showErrors(msg);
            } else {
              _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
            }
          },
        });
        return false;
      }
    });
  },

  editExport: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    var nfsExport = this.nfsExports.get(button.data('id'));
    $(this.el).html(this.editTemplate({ 
      share: this.share,
      nfsExport: nfsExport,
      modify_choices: this.modify_choices,
      sync_choices: this.sync_choices,
    }));
    var validator = this.$("#edit-nfs-export-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        host_str: "required"
      },
      submitHandler: function() {
        var button = _this.$('#update-export');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
          url: "/api/shares/"+_this.share.get('name')+'/nfs/' + nfsExport.id,
          type: "PUT",
          dataType: "json",
          data: {
            host_str: _this.$("#host_str").val(),
            mod_choice: _this.$("#mod_choice").val(),  
            sync_choice: _this.$("#sync_choice").val()  
          },
          success: function() {
            _this.render();
          },
          error: function(xhr, status, error) {
            enableButton(button);
            var msg = parseXhrError(xhr)
            if (_.isObject(msg)) {
              validator.showErrors(msg);
            } else {
              _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
            }
          },
        });
        return false;
      }
    });
  },

  deleteExport: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    var exportId = button.data('id');
    var hostStr = button.data('hoststr');
    if(confirm("Delete nfs export for  " + hostStr + ". Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/shares/" + _this.share.get('name') + '/nfs/' + exportId,
        type: "DELETE",
        dataType: "json",
        success: function() {
          enableButton(button)
          _this.render();
        },
        error: function(xhr, status, error) {
          enableButton(button)
          var msg = parseXhrError(xhr)
          _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
        },
      });
    }
  },

  cancel: function(event) {
    event.preventDefault();
    this.render();
  },

  disableAddButton: function() {
    this.$('#add-export').addClass('disabled');
  },

  enableAddButton: function() {
    this.$('#add-export').removeClass('disabled');
  },

});


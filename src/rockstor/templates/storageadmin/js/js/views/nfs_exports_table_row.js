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

NFSExportsTableRow  = RockstoreModuleView.extend({
  tagName: "tr",

  events: {
    'click .edit-row':      'editRow',
    'click .delete-row':    'deleteRow',
    'click .save-row':    'saveRow',
    'click .cancel-edit':      'cancelEdit',
  },

  
  initialize: function() {
    this.nfs_export = this.options.nfs_export;
    this.index = this.options.index;
    this.share = this.options.share;
    this.parentView = this.options.parentView;
    this.modify_choices = this.options.modify_choices;
    this.sync_choices = this.options.sync_choices;
    this.show_template = window.JST.share_nfs_exports_table_row_show_template;
    this.edit_template = window.JST.share_nfs_exports_table_row_edit_template;

  },

  render: function() {
    $(this.el).empty();
    $(this.el).append(this.show_template({
      nfs_export: this.nfs_export,
      index: this.index,
      share: this.share,
    }));
    return this;
  },

  editRow: function(event) {
    event.preventDefault();
    $(this.el).empty();
    $(this.el).append(this.edit_template({
      nfs_export: this.nfs_export,
      index: this.index,
      share: this.share,
      modify_choices: this.modify_choices,
      sync_choices: this.sync_choices
    }));
  },

  deleteRow: function(event) {
    event.preventDefault();
    var button = this.$('.delete-row');
    if (buttonDisabled(button)) return false;
    var _this = this;
    data = {id: this.nfs_export.id};
    if(confirm("Delete nfs : "+ this.nfs_export.id +"...Are you sure?")){
    disableButton(button);
    $.ajax({
      url: "/api/shares/"+_this.share.get('name')+'/nfs/' + this.nfs_export.id,
      type: "DELETE",
      dataType: "json",
      data: data,
      success: function() {
        enableButton(button)
        _this.parentView.render();
      },
      error: function(xhr, status, error) {
        enableButton(button)
        var msg = parseXhrError(xhr)
        if (_.isObject(msg)) {
          _this.validator.showErrors(msg);
        } else {
          _this.parentView.$(".messages").html("<label class=\"error\">" + msg + "</label>");
        }
      },
    });
    }
  },

  saveRow: function(event) {
    event.preventDefault();
    var _this = this;
    data = $(this.el).getJSON();
    $.ajax({
      url: "/api/shares/"+_this.share.get('name')+'/nfs-update/',
      type: "PUT",
      dataType: "json",
      data: data,
      success: function() {
        _this.share.fetch();
      },
      error: function(request, status, error) {
        showError(request.responseText);
      },
    });
  },

  cancelEdit: function(event) {
    event.preventDefault();
    $(this.el).empty();
    $(this.el).append(this.show_template({
      nfs_export: this.nfs_export,
      index: this.index,
      share: this.share,
    }));

  }


});


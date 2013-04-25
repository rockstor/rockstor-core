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

NFSExportsTableModule  = RockstoreModuleView.extend({
  events: {
    'click #add-export': 'addRow',
    'click #cancel-add': 'cancelAdd',
    'click #save-new': 'saveNew',
  },

  initialize: function() {
    this.template = window.JST.share_nfs_exports_table_template;
    this.module_name = 'nfs_exports';
    this.share = this.options.share;
    this.nfs_exports = new NFSExportCollection();
    this.nfs_exports.setUrl(this.share.get('shareName'));
    this.add_row_template = window.JST.share_nfs_exports_table_row_template;
    this.empty_template = window.JST.share_nfs_exports_table_empty_body_template;
    this.modify_choices = this.options.modify_choices;
    this.sync_choices = this.options.sync_choices;
    this.share.on('change', function() {
      this.nfs_exports.reset(this.share.get('nfs_exports'));
    }, this)
  },

  render: function() {
    var _this = this;
    this.nfs_exports.fetch({
      success: function(collection, response, options) {
        $(_this.el).empty();
        $(_this.el).append(_this.template({
          share: _this.share,
          nfs_exports: _this.nfs_exports,
        }));
        _this.nfs_exports.each(function(nfs_export, index) {
          var nfs_export_row = new NFSExportsTableRow({
            nfs_export: nfs_export,
            index: index,
            share: this.share,
            modify_choices: this.modify_choices,
            sync_choices: _this.sync_choices,
            parentView: _this

          });
          _this.$('#nfs-exports-table-body').append(nfs_export_row.render().el);
        }, _this);

      },
      error: function(collection, response, options) {
        logger.debug('error while fetching nfs exports');
        logger.debug(response);
      }
    });
    return this;
  },

  addRow: function(event) {
    event.preventDefault();
    var button = $(event.currentTarget);
    if (!button.hasClass('disabled')) {
      if (this.nfs_exports.length == 0) {
        // remove 'no exports' message from body
        this.$('#nfs-exports-table-body').empty();
      }
      this.$('#nfs-exports-table-body').append(this.add_row_template({
        modify_choices: this.modify_choices,
        sync_choices: this.sync_choices
      }));
    }
    this.disableAddButton();
  },

  cancelAdd: function(event) {
    event.preventDefault();
    this.$('#new-nfs-export-row').remove();
    this.enableAddButton();
    if (this.nfs_exports.length == 0) {
      this.$('#nfs-exports-table-body').empty().append(this.empty_template());
    }
  },

  disableAddButton: function() {
    this.$('#add-export').addClass('disabled');
  },

  enableAddButton: function() {
    this.$('#add-export').removeClass('disabled');
  },

  saveNew: function() {
    var button = this.$('#save-new');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var _this = this;
    data = $('#new-nfs-export-row').getJSON();
    console.log(data);
    $.ajax({
      url: "/api/shares/"+_this.share.get('name')+'/nfs/',
      type: "POST",
      dataType: "json",
      data: data,
      success: function() {
        _this.render();
      },
      error: function(request, status, error) {
        enableButton(button);
        showError(request.responseText);
      },
    });


  },

});


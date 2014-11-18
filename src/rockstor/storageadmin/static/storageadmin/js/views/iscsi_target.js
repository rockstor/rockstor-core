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

var ISCSITargetView = Backbone.View.extend({

  events: {
    'click #add-iscsi-target': 'addIscsiTarget',
    'click #save-new': 'saveNew',
    'click #cancel-add': 'cancelAdd',
  },

  initialize: function() {
    this.template = window.JST.share_iscsi_target_template;
    this.add_template = window.JST.share_add_iscsi_target_template;
    this.empty_template = window.JST.share_iscsi_target_empty_row_template;
    this.share = this.options.share;
    this.iscsi_target = this.options.iscsi_target;
  },

  render: function() {
   $(this.el).empty();
    $(this.el).append(this.template({
      share: this.share,
      iscsi_target: this.iscsi_target
    }));
    return this;
  },

  addIscsiTarget: function(event) {
    event.preventDefault();
    var button = $(event.currentTarget);
    if (!button.hasClass('disabled')) {
      this.$('#iscsi-target-table-body').html(this.add_template());
      this.disableAddButton();
    }
  },

  cancelAdd: function(event) {
    event.preventDefault();
    this.$('#new-row').remove();
    this.enableAddButton();
    this.$('#iscsi-target-table-body').append(this.empty_template());
  },

  saveNew: function(event) {
    event.preventDefault();
    var _this = this;
    data = this.$('#iscsi-row').getJSON();
   this.iscsi_target.save(
      data,
      {
        success: function(model, response, options) {
          _this.render();
        },
        error: function(model, xhr, options) {
          showError(xhr.responseText);
        }
      }
    );

  },

  deleteIscsiTarget: function(event) {
    event.preventDefault();
    if (!this.iscsi_target.isNew()) {
      this.iscsi_target.destroy({
        success: function(model, response, options) {
          _this.iscsi_target = new ISCSITarget({shareName: this.share.get('shareName')});
          _this.render();
        },
        error: function(model, xhr, options) {
          showError(xhr.responseText);
        },

      });
    }

  },

  disableAddButton: function() {
    this.$('#add-iscsi-target').addClass('disabled');
  },

  enableAddButton: function() {
    this.$('#add-iscsi-target').removeClass('disabled');
  },

});


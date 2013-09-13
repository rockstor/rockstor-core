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

SnapshotsTableModule  = RockstoreModuleView.extend({
  events: {
    "click #js-snapshot-add": "add",
    "click #js-snapshot-save": "save",
    "click #js-snapshot-cancel": "cancel",
    "click .js-snapshot-delete": "deleteSnapshot"
  },

  initialize: function() {
    this.template = window.JST.share_snapshots_table_template;
    this.addTemplate = window.JST.share_snapshot_add;
    this.module_name = 'snapshots';
    this.share = this.options.share;
    this.snapshots = this.options.snapshots;
  },

  render: function() {
    var _this = this;
    $(this.el).empty();
    $(this.el).append(this.template({
      snapshots: this.snapshots,
      share: this.share
    }));
    this.$('#snapshots-table').tablesorter();
    this.$('button[data-action=delete]').click(function(event) {
    });
    return this;
  },
  setShareName: function(shareName) {
      this.snapshots.setUrl(shareName);
  },

  add: function(event) {
    event.preventDefault();
    $(this.el).html(this.addTemplate({
      snapshots: this.snapshots,
      share: this.share
    }));
  },

  save: function(event) {
    event.preventDefault();
    var _this = this;
    var button = this.$('#js-snapshot-save');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    $.ajax({
      url: "/api/shares/" + this.share.get('name') + "/snapshots/" + this.$('#snapshot-name').val(),
      type: "POST",
      dataType: "json",
      success: function() {
        enableButton(button);
        _this.snapshots.fetch({
          success: function() { _this.render(); }
        });
      },
      error: function(request, status, error) {
        enableButton(button);
        var msg = parseXhrError(error)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });
  },

  deleteSnapshot: function(event) {
    event.preventDefault();
    var _this = this;
    name = $(event.currentTarget).attr('data-name');
    share_name = this.share.get("name");
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    console.log('sending delete event');
    if(confirm("Delete snapshot:  "+ name +"...Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/shares/" + share_name + "/snapshots/" + name,
        type: "DELETE",
        success: function() {
          enableButton(button)
          _this.snapshots.fetch({
            success: function() { _this.render(); }
          });
        },
        error: function(request, status, error) {
          enableButton(button)
          var msg = parseXhrError(error)
          _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
        }
      });
    }
  },

  cancel: function(event) {
    event.preventDefault();
    this.render();
  },



});


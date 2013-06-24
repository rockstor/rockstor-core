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
  
  initialize: function() {
    this.template = window.JST.share_snapshots_table_template;
    this.module_name = 'snapshots';
    this.share = this.options.share;
  },

  render: function() {
    var _this = this;
    $(this.el).empty();
    $(this.el).append(this.template({
      snapshots: this.collection,
      share: this.share
    }));
    _this.$('#snapshots-table').tablesorter();
    this.$('button[data-action=delete]').click(function(event) {
      name = $(event.target).attr('data-name');
      share_name = $(event.target).attr('data-share-name');
      var button = $(event.target);
      if (buttonDisabled(button)) return false;
      console.log('sending delete event');
      if(confirm("Delete snapshot:  "+ name +"...Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/shares/" + share_name + "/snapshots/" + name + "/",
        type: "DELETE",
        success: function() {
          enableButton(button)
          _this.collection.fetch();
        },
        error: function(request, status, error) {
          enableButton(button)
          showError(request.responseTest);
        }
      });
      }
    });
    return this;
  },
  setShareName: function(shareName) {
      this.snapshots.setUrl(shareName);
  }
});


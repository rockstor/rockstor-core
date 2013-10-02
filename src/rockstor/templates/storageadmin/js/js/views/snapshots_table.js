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
    "click #js-snapshot-cancel": "cancel",
    "click .js-snapshot-delete": "deleteSnapshot"
  },

  initialize: function() {
    this.template = window.JST.share_snapshots_table_template;
    this.paginationTemplate = window.JST.common_pagination;
    this.addTemplate = window.JST.share_snapshot_add;
    this.module_name = 'snapshots';
    this.share = this.options.share;
    this.snapshots = this.options.snapshots;
    this.collection = this.options.snapshots;
    this.collection.on("reset", this.render, this);
  },

  render: function() {
    var _this = this;
    $(this.el).empty();
    $(this.el).append(this.template({
      snapshots: this.collection,
      share: this.share
    }));
    this.$('#snapshots-table').tablesorter();
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
    return this;
  },

  setShareName: function(shareName) {
      this.collection.setUrl(shareName);
  },

  add: function(event) {
    var _this = this;
    event.preventDefault();
    $(this.el).html(this.addTemplate({
      snapshots: this.collection,
      share: this.share
    }));
    this.validator = this.$('#add-snapshot-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        'snapshot-name': 'required',
      },
      submitHandler: function() {
        var button = _this.$('#js-snapshot-save');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
          url: "/api/shares/" + _this.share.get('name') + "/snapshots/" + _this.$('#snapshot-name').val(),
          type: "POST",
          dataType: "json",
          contentType: 'application/json',
          data: JSON.stringify({uvisible: _this.$('#snapshot-visible').prop('checked')}),
          success: function() {
            enableButton(button);
            _this.collection.fetch({
              success: function() { _this.render(); }
            });
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

  deleteSnapshot: function(event) {
    event.preventDefault();
    var _this = this;
    name = $(event.currentTarget).attr('data-name');
    share_name = this.share.get("name");
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    if(confirm("Delete snapshot:  "+ name +"...Are you sure?")){
      disableButton(button);
      $.ajax({
        url: "/api/shares/" + share_name + "/snapshots/" + name,
        type: "DELETE",
        success: function() {
          enableButton(button)
          _this.collection.fetch({
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

// Add pagination
Cocktail.mixin(SnapshotsTableModule, PaginationMixin);


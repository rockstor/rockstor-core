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

UsersView = RockstoreLayoutView.extend({
  events: {
    "click .delete-user": "deleteUser",
    "click .edit-user": "editUser"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.users_users;
    this.paginationTemplate = window.JST.common_pagination;
    this.collection = new UserCollection();
    this.dependencies.push(this.collection);
    this.collection.on("reset", this.renderUsers, this);
  },

  render: function() {
    this.collection.fetch();
    return this;
  },

  renderUsers: function() {
    if (this.$('[rel=tooltip]')) { 
      this.$('[rel=tooltip]').tooltip('hide');
    }
    $(this.el).html(this.template({users: this.collection}));
    this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
  },

  deleteUser: function(event) {
    event.preventDefault();
    var _this = this;
    var username = $(event.currentTarget).attr('data-username');
    if(confirm("Delete user:  "+ username +". Are you sure?")){
      $.ajax({
        url: "/api/users/"+username,
        type: "DELETE",
        dataType: "json",
        success: function() {
          _this.collection.fetch();
        },
        error: function(xhr, status, error) {
          var msg = parseXhrError(xhr)
          _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
        }
      });
    } else {
      return false;
    }
  },

  editUser: function(event) {
    if (event) event.preventDefault();
    if (this.$('[rel=tooltip]')) { 
      this.$('[rel=tooltip]').tooltip('hide');
    }
    var username = $(event.currentTarget).attr('data-username');
    app_router.navigate('users/' + username + '/edit', {trigger: true});
  }

});

// Add pagination
Cocktail.mixin(UsersView, PaginationMixin);


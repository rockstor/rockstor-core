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
    "click .user-admin": "updateUserAdmin"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.users_users;
    // add dependencies
    this.users = new UserCollection();
    this.dependencies.push(this.users);
    this.users.on("reset", this.renderUsers, this);
  },

  render: function() {
    this.users.fetch();
    return this;
  },

  renderUsers: function() {
    console.log("rendering Users");
    $(this.el).html(this.template({users: this.users}));
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
          _this.users.fetch();
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

  updateUserAdmin: function(event) {
    var _this = this;
    var cbox = $(event.currentTarget);
    var is_active = cbox.prop("checked");
    console.log(is_active);
    var user = this.users.get(cbox.attr("data-username"));
    // dont send password
    user.unset("password");
    user.save({is_active: is_active}, {
      success: function(model, response, options) {
        console.log("user saved successfully");
        _this.users.fetch({silent: true});
      },
      error: function(model, xhr, options) {
        // reset checkbox to previous value on error
        cbox.prop("checked", !is_active);
        var msg = parseXhrError(xhr)
        _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
      }
    });
  }

});

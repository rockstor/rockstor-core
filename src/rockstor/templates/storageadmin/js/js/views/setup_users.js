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

SetupUsersView = Backbone.View.extend({
  tagName: 'div',
  
  events: {
    'click #new-user': 'addNewUser',
    'click #cancel-new-user': 'cancelNewUser',
    'click .edit-user': 'editUser',
    'click .delete-user': 'deleteUser',
    'click #save-new-user': 'saveNewUser',
    'click #save-user': 'saveUser',
    'click #cancel-edit-user': 'cancelEditUser',
  },

  initialize: function() {

    this.template = window.JST.setup_setup_users;
    this.new_user_template = window.JST.setup_new_user;
    this.edit_user_template = window.JST.setup_edit_user;

  },

  render: function() {
    console.log('in setup_users render');
    this.users = new UserCollection();
    var _this = this;
    this.users.fetch({
      success: function(collection, response, options) {
        _this.renderUsers();
        _this.users.on('reset', _this.renderUsers, _this);
      },
      error: function(collection, xhr, options) {
        console.log('Could not fetch users in setup_users');
      }
    });
    return this;
  },

  renderUsers: function() {
    console.log('in setup_users renderUsers');
    $(this.el).html(this.template({users: this.users}));
  },

  addNewUser: function(event) {
    //this.$("#new-user-container").html(this.new_user_template());
    $(this.el).html(this.new_user_template());
  },

  cancelNewUser: function(event) {
    event.preventDefault();
    this.renderUsers();
  },

  editUser: function(event) {
    event.preventDefault();
    var tgt = $(event.currentTarget);
    $(this.el).html(this.edit_user_template({
      user: this.users.get(tgt.attr('data-id'))
    }));
  },
  
  cancelEditUser: function(event) {
    event.preventDefault();
    this.renderUsers();
  },

  deleteUser: function(event) {
    console.log('deleteUser clicked');
    event.preventDefault();
    var _this = this;
    var tgt = $(event.currentTarget);
    var user = new User({ 
      id: tgt.attr('data-id'),
      username: tgt.attr('data-username') 
    });
    user.destroy({
      success: function(model, response, options) {
        console.log('user deleted successfully');
        _this.users.fetch();
      },
      error: function(model, xhr, options) {
        var msg = xhr.responseText;
        console.log('error while deleting user');
        console.log(msg);
      }

    });

  },

  saveNewUser: function() {
    console.log('add-user clicked');
    var new_user = new User();
    username = this.$('#username').val();
    password = this.$('#password').val();
    password_confirmation = this.$('#password_confirmation').val();
    var user = new User();
    var _this = this;
    user.save(
      {
        username: this.$('#username').val(),
        password: this.$('#password').val()
      }, 
      {
        success: function(model, response, options) {
          console.log('new user created successfully');
          //_this.$('#new-user-container').empty();
          _this.users.fetch();

        },
        error: function(model, xhr, options) {
          var msg = xhr.responseText;
          try {
            msg = JSON.parse(msg).detail;
          } catch(err) {
          }
          _this.$('#add-user-msg').html(msg);

        }
      }
    );


  },

  saveUser: function(event) {
    var _this = this;
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    var tgt = $(event.currentTarget);
    var password = this.$('#password').val();
    var password_confirmation = this.$('#password_confirmation').val();
    var user = new User();
    user.save(
      { id: tgt.attr('data-id'), password: password } , 
      {
        success: function(model, response, options) {
          console.log('user updated successfully');
          _this.users.fetch();
        },
        error: function(model, xhr, options) {
          var msg = xhr.responseText;
          console.log('error while updating user');
          console.log(msg);
        }

      });
  }

});

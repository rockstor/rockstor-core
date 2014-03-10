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

EditUserView = RockstorLayoutView.extend({
  events: {
    "click #cancel": "cancel"
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.users_edit_user;
    this.username = this.options.username;
    this.user = new User({username: this.username});
    this.dependencies.push(this.user);
  },
  
  render: function() {
    this.fetch(this.renderUser, this);
    return this;
  },

  renderUser: function() {
    var _this = this;
    $(this.el).html(this.template({
      username: this.username,
      user: this.user

    }));

    this.validator = this.$("#change-password-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        password_confirmation: {
          equalTo: "#password"
        }
      },
      messages: {
        password_confirmation: {
          equalTo: "The passwords do not match"
        }
      },
      submitHandler: function() {
        var password = _this.$("#password").val().trim();
        var user = new User({username: _this.username});
        var is_active = _this.$('#is_active').prop('checked');
        if (!_.isEmpty(password)) {
          user.set({password: password});
        } else {
          user.unset('password');
        }
        user.set({is_active: is_active});
        user.save(null, {
          success: function(model, response, options) {
            app_router.navigate("users", {trigger: true});
          },
          error: function(model, xhr, options) {
          }
        });
        return false;  
      }
    });
  },

  cancel: function() {
    app_router.navigate("users", {trigger: true});
  }

});



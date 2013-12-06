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

LoginView = Backbone.View.extend({
  tagName: 'div',
  events: {
    'click #sign_in': 'login',
  },
  initialize: function() {
    this.login_template = window.JST.home_login_template;
    this.user_create_template = window.JST.home_user_create_template;
  },

  render: function() {
    var _this = this;
    if (RockStorGlobals.setup_user) {
    } else {
      $(this.el).append(this.user_create_template());
      this.validator = this.$("#user-create-form").validate({
        onfocusout: false,
        onkeyup: false,
        rules: {
          username: "required",
          password: "required",
          password_confirmation: {
            required: "true",
            equalTo: "#password"
          }
        },
        messages: {
          password_confirmation: {
            equalTo: "The passwords do not match"
          }
        },
        submitHandler: function() {
          var username = _this.$("#username").val();
          var password = _this.$("#password").val();
          var setupUserModel = Backbone.Model.extend({
            urlRoot: "/setup_user",
          });
          var user = new setupUserModel();
          user.save(
            {
              username: username,
              password: password,
              is_active: true
            },
            {
              success: function(model, response, options) {
                _this.makeLoginRequest(username, password);
              },
              error: function(model, xhr, options) {
              }
            }
          );
        }
      });
    }
    return this;
  },

  login: function(event) {
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    this.makeLoginRequest(
      this.$("#username").val(),
      this.$("#password").val());
  },
  
  makeLoginRequest: function(username, password) {
    var _this = this;
    $.ajax({
      url: "/api/login",
      type: "POST",
      dataType: "json",
      data: {
        username: username,
        password: password,
      }, 
      success: function(data, status, xhr) {
        logged_in = true;
        refreshNavbar();
        app_router.navigate('home', {trigger: true}) 
      },
      error: function(xhr, status, error) {
        _this.$(".messages").html("<label class=\"error\">Login incorrect!</label>");
      }
    });

  },

});

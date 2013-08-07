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
    'click #create_user': 'createUser',
  },
  initialize: function() {
    this.login_template = window.JST.home_login_template;
    this.user_create_template = window.JST.home_user_create_template;
  },

  render: function() {
    console.log("rendering LoginView");
    if (RockStorGlobals.setup_user) {
      $(this.el).append(this.login_template());
    } else {
      $(this.el).append(this.user_create_template());
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
    $.ajax({
      url: "/api/login",
      type: "POST",
      dataType: "json",
      data: {
        username: username,
        password: password,
      }, 
      success: function(data, status, xhr) {
        console.log("logged in successfully");
        logged_in = true;
        refreshNavbar();
        app_router.navigate('home', {trigger: true}) 
      },
      error: function(xhr, status, error) {
        showError(xhr.responseText);	
      }
    });

  },

  createUser: function(event) {
    var _this = this;
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    var username = this.$("#username").val();
    var password = this.$("#password").val();
    console.log("Create user clicked");
    $.ajax({
      url: "/setup_user",
      type: "POST",
      dataType: "json",
      data: {
        username: username,
        password: password,
        utype: "admin"
      }, 
      success: function(data, status, xhr) {
        console.log("created user successfully");
        _this.makeLoginRequest(username, password);
      },
      error: function(xhr, status, error) {
        showError(xhr.responseText);	
      }
    });

  }

});

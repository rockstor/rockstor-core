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

AddUserView = RockstoreLayoutView.extend({

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.users_add_user;
  },

  render: function() {
    var _this = this;
    $(this.el).html(this.template());

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
        var utype = _this.$("#admin").prop("checked") ? "admin" : ""; 
        $.ajax({
          url: "/api/users/",
          type: "POST",
          dataType: "json",
          data: {
            username: username,
            password: password,
            utype: utype
          }, 
          success: function(data, status, xhr) {
            console.log("user created successfully");
            app_router.navigate("users", {trigger: true});
          },
          error: function(xhr, status, error) {
            var msg = xhr.responseText;
            var fieldName = null;
            try {
              msg = JSON.parse(msg).detail;
            } catch(err) {
            }
            if (typeof(msg)=="string") {
              try {
                msg = JSON.parse(msg);
              } catch(err) {
              }
            }
            if (_.isObject(msg)) {
              fieldName = _.keys(msg)[0];
              msg = msg[fieldName];
            }
            if (fieldName) {
              e = {};
              e[fieldName] = msg;
              _this.validator.showErrors(e);
            } else {
              _this.$(".messages").html("<label class=\"error\">" + msg + "</label>");
            }
          }
        });
      }
    });
    return this;
  },

  cancel: function() {
    app_router.navigate("users", {trigger: true});
  }

});


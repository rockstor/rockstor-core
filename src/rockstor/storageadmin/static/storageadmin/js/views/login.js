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
    this.networkInterfaces = new NetworkInterfaceCollection();
    this.networkInterfaces.pageSize = RockStorGlobals.maxPageSize;
    this.networkInterfaces.on("reset", this.saveAppliance, this);
    this.appliances = new ApplianceCollection();
    version_update = false;
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
          hostname: "required",
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
          RockStorGlobals.hostname = _this.$('#hostname').val();
            
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
            	console.log("in success");
                $('#update-version-modal').modal({
               		keyboard: false,
               		backdrop: 'static',
               		show: false
               	});
               	$('#update-version-modal').modal('show'); 
                $('#update-version-modal #updateYes').click(function(event) {
                	console.log("in click");
                    console.log('update yes clicked');
                      version_update = true;
                     	$('#update-version-modal').modal('hide'); 
              //      _this.makeLoginRequest(username, password);
            //logged_in = true;
            //refreshNavbar();
            //app_router.navigate('home', {trigger: true}) 
              
              });
               $('#update-version-modal').on('hide.bs.modal', function () {
              	console.log('modal close event called');
                	_this.makeLoginRequest(username, password);
                	});
               
             
               },
              error: function(model, xhr, options) {
              }
            }
          );
          
          return false;
        }
      });
    }
    return this;
  },

  login: function(event) {
    if (!_.isUndefined(event) && !_.isNull(event)) {
      event.preventDefault();
    }
    this.makeLoginRequest(this.$("#username").val(), this.$("#password").val());
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
    	  _this.scanNetwork();
     
      },
      error: function(xhr, status, error) {
        _this.$(".messages").html("<label class=\"error\">Login incorrect!</label>");
      }
    });
  },
  
  scanNetwork: function() {
    var _this = this;
    $.ajax({
      url: "/api/network", 
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        _this.networkInterfaces.fetch();
      },
      error: function(xhr, status, error) {
        logger.debug(error);
      }
    });
  },
  
  setIp: function() {
    var mgmtIface = this.networkInterfaces.find(function(iface) {
      return iface.get('itype') == 'management';
    });
    if (!_.isUndefined(mgmtIface)) {
      RockStorGlobals.ip = mgmtIface.get("ipaddr");
    } else {
      RockStorGlobals.ip = this.networkInterfaces.at(0).get("ipaddr");
    }
  },
  
  saveAppliance: function() {
    var _this = this;
    
    this.setIp();

    // create current appliance if not created already
    if (this.appliances.length > 0) {
      var current_appliance = this.appliances.find(function(appliance) {
        return appliance.get('current_appliance') == true; 
      })
    }
    if (_.isUndefined(current_appliance)) {
      var new_appliance = new Appliance();
      new_appliance.save(
        {
          hostname: RockStorGlobals.hostname,
          ip: RockStorGlobals.ip,
          current_appliance: true
        },
        {
          success: function(model, response, options) {
            setup_done = true;
            _this.scanDisks();
         },
          error: function(model, xhr, options) {
            var msg = xhr.responseText;
            try {
              msg = JSON.parse(msg).detail;
            } catch(err) {
            }
          }
        }
      );
    } else {
    	app_router.navigate('home', {trigger: true}) ;
    }
  },
  
  scanDisks: function() {
    var _this = this;
     $.ajax({
      url: "/api/disks/scan",
      type: "POST"
    }).done(function() {
      _this.goToRoot();
    });
  },

  goToRoot: function() {
    if(version_update){ 
    	console.log('in goto root function');
    	console.log(version_update);
    	 window.location.replace('/version');
    }else{
    	 window.location.replace("/");
    }
  },
  

});

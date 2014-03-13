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

SetupView = RockstorLayoutView.extend({
  tagName: 'div',
  
  events: {
    'click #next-page': 'nextPage',
    'click #prev-page': 'prevPage',
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.setup_setup;
    this.pages = [null, SetupDisksView, SetupSystemView];
    this.sidebars = [null, "disks"];
    this.current_page = 1;
    this.current_view = null;
    this.appliances = new ApplianceCollection();
    this.appliances.pageSize = RockStorGlobals.maxPageSize;
    this.dependencies.push(this.appliances);
    this.networkInterfaces = new NetworkInterfaceCollection();
    this.networkInterfaces.pageSize = RockStorGlobals.maxPageSize;
    this.networkInterfaces.on("reset", this.saveAppliance, this);

  },

  render: function() {
    $(this.el).html(this.template());
    var _this = this;
    this.fetch(this.renderCurrentPage, this);
    return this;
  },

  renderCurrentPage: function() {
    opts = {
      appliances: this.appliances
    };
    this.renderSidebar("setup", this.sidebars[this.current_page]);
    this.current_view = new this.pages[this.current_page](opts);
    this.$('#current-page-inner').html(this.current_view.render().el);

  },

  nextPage: function() {
    if (this.current_page < this.pages.length-1) {
      this.current_page = this.current_page + 1;
      this.renderCurrentPage();
      this.modifyButtonText();
      this.setCurrentStepTitle(this.current_page, this.current_page-1);
    } else {
      this.save();
    }
  },

  prevPage: function() {
    if (this.current_page > 1) {
      this.current_page = this.current_page - 1;
      this.renderCurrentPage();
      this.modifyButtonText();
      this.setCurrentStepTitle(this.current_page, this.current_page+1);
    }
  },

  modifyButtonText: function() {
    if (this.lastPage()) {
      this.$('#next-page').html('Finish');
    } else {
      this.$('#next-page').html('Next');
    }
  },

  lastPage: function() {
    return (this.current_page == (this.pages.length - 1));
  },
  
  save: function() {
    // hostname is the last page, so check if the form is filled
    this.current_view.$('#set-hostname-form').submit();
    if (!_.isUndefined(RockStorGlobals.hostname) &&
        !_.isNull(RockStorGlobals.hostname)) {
      var button = this.$('#next-page');
      if (buttonDisabled(button)) return false;
      disableButton(button);
      this.scanNetwork();
    }
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
            //app_router.navigate('home', {trigger: true});

            window.location.replace("/")
          },
          error: function(model, xhr, options) {
            var msg = xhr.responseText;
            try {
              msg = JSON.parse(msg).detail;
            } catch(err) {
            }
            console.log(msg);
          }
        }
      );
    } else {
      app_router.navigate('home', {trigger: true});
    }
  },

  setCurrentStepTitle: function(new_step, old_step) {
      old_step_str = old_step + '';
      old_sel_str = '#setup-titles li[data-step="' + old_step_str + '"]';
      this.$(old_sel_str).removeClass('current-step');
      new_step_str = new_step + '';
      new_sel_str = '#setup-titles li[data-step="' + new_step_str + '"]';
      this.$(new_sel_str).addClass('current-step');
  },

  renderSidebar: function(name, selected) {
    var sidenavTemplate = window.JST["common_sidenav_" + name];
    $("#sidebar-inner").html(sidenavTemplate({selected: selected}));
  },


});


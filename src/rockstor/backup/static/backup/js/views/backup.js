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

BackupView = RockstoreLayoutView.extend({
  
  events: {
    'click .slider-stop': "stopService",
    'click .slider-start': "startService",
    'click .delete-policy': "deletePolicy",
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    // set template
    this.template = window.JST.backup;
    this.serviceTemplate = window.JST.backup_service;
    this.policyTableTemplate = window.JST.policy_table;
    this.paginationTemplate = window.JST.common_pagination;
    // add dependencies
    this.collection = new BackupPolicyCollection();
    this.dependencies.push(this.collection);
    this.backupPolicyTrails = new BackupPolicyTrailCollection();
    this.backupPolicyTrails.pageSize = RockStorGlobals.maxPageSize;
    this.dependencies.push(this.backupPolicyTrails);
    this.status = new BackupPluginStatus();
    this.dependencies.push(this.status);
    this.trailMap = {};
  },

  render: function() {
    this.fetch(this.renderBackupPolicies, this);
    return this;
  },

  renderBackupPolicies: function() {
    var _this = this;
    
    this.collection.each(function(policy, index) {
      var tmp = _this.backupPolicyTrails.filter(function(trail) {
        return trail.get('policy') == policy.id;
      });
      _this.trailMap[policy.id] = _.sortBy(tmp, function(trail) {
        return moment(trail.get('start')).valueOf();
      }).reverse();
    });
    
    $(this.el).html(this.template({ 
      collection: this.collection,
      status: this.status
    }));
    this.$("#policy-table-ph").html(this.policyTableTemplate({
      collection: this.collection,
      trailMap: this.trailMap
    }));
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
    this.$('#service-ph').html(_this.serviceTemplate({status: this.status}));
    this.$('input.service-status').simpleSlider({
      "theme": "volume",
      allowedValues: [0,1],
      snap: true 
    });
    this.$('input.service-status').each(function(i, el) {
      var slider = $(el).data('slider-object');
      // disable track and dragger events to disable slider
      slider.trackEvent = function(e) {};
      slider.dragger.unbind('mousedown');
    });
    return this;
  }, 
  
  startService: function(event) {
    var _this = this;
    // if already started, return
    if (this.getSliderVal().toString() == "1") return; 
    this.setStatusLoading(true);
    $.ajax({
      url: '/api/plugin/backup/plugin/start',
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        _this.highlightStartEl(true);
        _this.setSliderVal(1); 
        _this.setStatusLoading(false);
      },
      error: function(xhr, status, error) {
        // TODO fix global error handler to show popup
        // depending on flag from server side.
      }
    });
  },
  
  stopService: function(event) {
    var _this = this;
    // if already stopped, return
    if (this.getSliderVal().toString() == "0") return; 
    this.setStatusLoading(true);
    $.ajax({
      url: '/api/plugin/backup/plugin/stop',
      type: "POST",
      dataType: "json",
      success: function(data, status, xhr) {
        _this.highlightStartEl(false);
        _this.setSliderVal(0); 
        _this.setStatusLoading(false);
      },
      error: function(xhr, status, error) {
        // TODO fix global error handler to show popup
        // depending on flag from server side.
      }
    });
  },
  
  setSliderVal: function(val) {
    this.$('input.service-status').simpleSlider('setValue',val);
  },
  
  highlightStartEl: function(on) {
    var el = this.$('div.slider-start');
    on ? el.addClass('on') : el.removeClass('on');
  },
  
  getSliderVal: function() {
    return this.$('input.service-status').data('slider-object').value;
  },
  
  setStatusLoading: function(serviceName, show) {
    var el = this.$('div.command-status');
    var img = $('<img src="/static/storageadmin/img/ajax-loader.gif"></img>');
    show ? el.html(img) : el.empty();
  },
  
  deletePolicy: function(event) {
    event.preventDefault();
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    var policyId = button.attr('data-policy-id');
    if(confirm("Delete policy ... Are you sure?")){
      disableButton(button);	
      $.ajax({
        url: "/api/plugin/backup/" + policyId,
        type: "DELETE",
        dataType: "json",
        success: function() {
          _this.render();
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });
    }
  }
});

// Add pagination
Cocktail.mixin(BackupView, PaginationMixin);

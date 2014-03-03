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
    
    $(this.el).html(this.template({ collection: this.collection }));
    this.$("#policy-table-ph").html(this.policyTableTemplate({
      collection: this.collection,
      trailMap: this.trailMap
    }));
    this.$(".pagination-ph").html(this.paginationTemplate({
      collection: this.collection
    }));
    var jqXhr = $.ajax({
      url: '/api/plugin/backup/plugin/status',
      type: 'POST',
      dataType: 'json'
    }).done(function(data, status, jqXhr) {
      _this.$('#service-ph').html(_this.serviceTemplate({status: data}));
      _this.$('input.service-status').simpleSlider({
        "theme": "volume",
        allowedValues: [0,1],
        snap: true 
      });
    })
    return this;
  },

 deleteBackup: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    name = button.attr('data-name');
    if(confirm("Delete policy ... Are you sure?")){
      disableButton(button);	
      $.ajax({
        url: "/api/backup/" + ip,
        type: "DELETE",
        dataType: "json",
        data: { "ip": ip },
        success: function() {
          _this.render();
          enableButton(button);
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

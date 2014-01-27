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
    this.template = window.JST.backup_backup;
    this.paginationTemplate = window.JST.common_pagination;
    // add dependencies
    this.collection = new BackupPolicyCollection();
    this.collection.on("reset", this.renderBackups, this);
    
  },

  render: function() {
    this.fetch(this.renderBackups, this);
    return this;
  },

  renderBackups: function() {

    var _this = this;
    
    $(this.el).html(this.template({ collection: this.collection }));
    this.$("#policy-table-ph").html(this.policy_table_template({
      collection: this.collection
    }));
    this.$(".pagination-ph").html(this.pagination_template({
      collection: this.collection
    }));
    this.$("#policy-table").tablesorter();
    this.$('#policy-table-ph-form :input').tooltip();
   
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

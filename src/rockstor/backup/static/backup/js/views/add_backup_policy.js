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

/*
 * Add Backup Policy View 
 */

AddBackupPolicyView = Backbone.View.extend({
  
   events: {
    "click #js-cancel": "cancel"
    },


  initialize: function() {
    this.backup = new BackupPolicyCollection();
  },
  render: function() {
    $(this.el).empty();
    this.template = window.JST.backup_add_backup_policy;
    var _this = this;
    this.backup.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({backup: _this.backup}));
        
      $('#add-backup-policy-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        
      },
        submitHandler: function() {
            var button = _this.$('#create-backup-policy');
              if (buttonDisabled(button)) return false;
              disableButton(button);
              $.ajax({
                 url: "/api/backup",
                 type: "PUT",
                 dataType: "json",
                 data: {"ip": server_ip, "path": export_path, "share": dest_share,"nlevel":notification_level, "email": notification_email, "stime": start_time},
                 success: function() {
                    app_router.navigate('backup', {trigger: true}) 
                 },
                 error: function(request, status, error) {
                   showError(request.responseText);	
                 },
               });
              }
             }); 
             } 
           });
       return this;
     },

  cancel: function(event) {
    event.preventDefault();
    app_router.navigate('backup', {trigger: true}) 
  }

});



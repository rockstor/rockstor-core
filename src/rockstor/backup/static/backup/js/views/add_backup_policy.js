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

AddBackupPolicyView = RockstoreLayoutView.extend({
  
  events: {
    "click #js-cancel": "cancel"
  },
  
  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.add_backup_policy;
    this.shares = new ShareCollection();
    this.dependencies.push(this.shares);
  },
  
  render: function() {
    this.fetch(this.renderPolicies, this);
    return this;
  },
  
  renderPolicies: function() {
    $(this.el).empty();
    var _this = this;
    $(_this.el).append(_this.template({shares: this.shares}));
    this.$('#add-backup-policy-form :input').tooltip({
      placement: 'right', html: true
    });
    this.$('#start_date').datepicker();
    var timePicker = this.$('#start_time').timepicker();
    this.$('#add-backup-policy-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        name: 'required',
        server_ip: 'required',
        export_path: 'required',
        dest_share: 'required',
        notification_level: 'required',
        start_date: 'required',
        start_time: 'required',
        frequency: 'required',
        num_retain: 'required'
      },
      submitHandler: function() {
        var button = $('#create-backup-policy');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var data = _this.$('#add-backup-policy-form').getJSON();
        var ts = moment(data.start_date, 'MM/DD/YYYY');
        var tmp = _this.$('#start_time').val().split(':')
        ts.add('h',tmp[0]).add('m', tmp[1]);
        data.ts = ts.unix();
        $.ajax({
          url: "/api/plugin/backup",
          type: "POST",
          dataType: "json",
          contentType: 'application/json',
          data: JSON.stringify(data),
          success: function() {
            enableButton(button);
            app_router.navigate('backup', {trigger: true}) 
          },
          error: function(xhr, status, error) {
            enableButton(button);
          },
        });
        return false;
      }
    });
    return this;
  },
    
  cancel: function(event) {
    event.preventDefault();
    app_router.navigate('backup', {trigger: true});
  }
});

// Add pagination
Cocktail.mixin(AddBackupPolicyView, PaginationMixin);


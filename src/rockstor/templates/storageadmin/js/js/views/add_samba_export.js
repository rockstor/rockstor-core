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

AddSambaExportView = RockstoreLayoutView.extend({
  events: {
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.samba_add_samba_export;
    this.shares = new ShareCollection();
    // dont paginate shares for now
    this.shares.pageSize = 1000; 
    this.dependencies.push(this.shares);
    this.yes_no_choices = [
      {name: 'yes', value: 'yes'},
      {name: 'no', value: 'no'}, 
    ];
    this.browsable_choices = this.yes_no_choices;
    this.guest_ok_choices = this.yes_no_choices;
    this.read_only_choices = this.yes_no_choices;
  },


  render: function() {
    this.fetch(this.renderSambaForm, this);
    return this;
  },

  renderSambaForm: function() {
    var _this = this;
    $(this.el).html(this.template({
      shares: this.shares,
      browsable_choices: this.browsable_choices,
      guest_ok_choices: this.guest_ok_choices,
      read_only_choices: this.read_only_choices
    }));

    $('#add-samba-export-form :input').tooltip();
    
    $('#add-samba-export-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        share: 'required',  
      },
      
      submitHandler: function() {
        var button = $('#create-samba-export');
        if (buttonDisabled(button)) return false;
        disableButton(button);

        console.log(JSON.stringify(_this.$('#add-samba-export-form').getJSON()));
        $.ajax({
          url: '/api/shares/' + _this.$('#share').val() + '/samba',
          type: 'POST',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(_this.$('#add-samba-export-form').getJSON()),
          success: function() {
            enableButton(button);
            app_router.navigate('samba-exports', {trigger: true});
          },
          error: function(xhr, status, error) {
            enableButton(button);
          }
        });
       
        return false;
      }
    });
  },
  
  cancel: function(event) {
    event.preventDefault();
    app_router.navigate('samba-exports', {trigger: true});
  }

});

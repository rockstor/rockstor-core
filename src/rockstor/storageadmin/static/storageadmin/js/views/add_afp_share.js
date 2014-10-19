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

AddAFPShareView = RockstorLayoutView.extend({
  events: {
    "click #cancel": "cancel"
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.afp_add_afp_share;
    this.shares = new ShareCollection();
    // dont paginate shares for now
    this.shares.pageSize = 1000; 
    this.dependencies.push(this.shares);
    //this.afpShares = new AFPCollection();
  //  this.dependencies.push(this.afpShares);
    this.modify_choices = [
      {name: 'ro', value: 'ro'}, 
      {name: 'rw', value: 'rw'},
    ];
  },
  
  render: function() {
    this.fetch(this.renderAFPForm, this);
    return this;
  },

  renderAFPForm: function() {
    var _this = this;
    //this.freeShares = this.shares.reject(function(share) {
     // s = this.sftpShares.find(function(afpShare) {
     //   return (afpShare.get('share') == share.get('name'));
    //  });
    //  return !_.isUndefined(s);
   // }, this);
    $(this.el).html(this.template({
      shares: this.shares,
    }));
    this.$('#shares').chosen();
    
    $('#add-afp-share-form :input').tooltip();
    
    $('#add-afp-share-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        shares: 'required',  
      },
      
      submitHandler: function() {
        var button = $('#create-afp-share');
        if (buttonDisabled(button)) return false;
        var data = _this.$('#add-afp-share-form').getJSON();
        if (data['read_only'] == "false") {
          delete data['read_only'];
        } else {
         data['read_only'] = true;
        } 
        console.log(data);
        disableButton(button);
        $.ajax({
          url: '/api/afp',
          type: 'POST',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(data),
          success: function() {
            enableButton(button);
            app_router.navigate('afp', {trigger: true});
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
    app_router.navigate('afp', {trigger: true});
  }

});




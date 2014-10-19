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
    this.afpShareId = this.options.afpShareId;
    this.afpShares = new AFPCollection();
    this.dependencies.push(this.afpShares);
     this.yes_no_choices = [
      {name: 'yes', value: 'yes'},
      {name: 'no', value: 'no'}, 
    ];
    this.time_machine_choices = this.yes_no_choices;
  },
  
  render: function() {
    this.fetch(this.renderAFPForm, this);
    return this;
  },

  renderAFPForm: function() {
    var _this = this;
    this.freeShares = this.shares.reject(function(share) {
      s = this.afpShares.find(function(afpShare) {
        return (afpShare.get('share') == share.get('name'));
      });
      return !_.isUndefined(s);
    }, this);
    
     if(this.afpShareId != null){
      this.aShares = this.afpShares.get(this.afpShareId);
      }else{
      this.aShares = null;
      }
    
    $(this.el).html(this.template({
      shares: this.freeShares,
      afpShare: this.aShares,
      afpShareId: this.afpShareId,
      time_machine_choices: this.time_machine_choices,
    }));
    this.$('#shares').chosen();
    
    $('#add-afp-share-form :input').tooltip({
     html: true,
     placement: 'right'
    });
    
    $('#add-afp-share-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        shares: 'required',  
      },
      
      submitHandler: function() {
        var button = $('#create-afp-export');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var submitmethod = 'POST';
        var posturl = '/api/netatalk';
        if(_this.afpShareId != null){
            submitmethod = 'PUT';
            posturl += '/'+_this.afpShareId;
          }
         $.ajax({
          url: posturl,
          type: submitmethod,
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(_this.$('#add-afp-share-form').getJSON()),
          success: function() {
            enableButton(button);
            _this.$('#add-afp-share-form :input').tooltip('hide');
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
    this.$('#add-afp-share-form :input').tooltip('hide');
    app_router.navigate('afp', {trigger: true});
  }

});




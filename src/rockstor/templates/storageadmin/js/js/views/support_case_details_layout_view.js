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

SupportCaseDetailsLayoutView = RockstoreLayoutView.extend({

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.supportCaseId = this.options.supportCaseId;
    this.template = window.JST.support_support_details_layout;
   
    this.support = new SupportCase({supportCaseId: this.supportCaseId});
    this.dependencies.push(this.support);
 
  },

  render: function() {
    this.fetch(this.renderSubViews, this);
    return this;

  },

 deleteSupportCase: function() {
    var _this = this;
    console.log('deleting ' + this.supportCase.get('id'));
    if(confirm("Delete support case :  "+ this.support.get('id') +"Are you sure?")){
    $.ajax({
      url: "/api/support/",
      type: "DELETE",
      dataType: "json",
      data: { "id": this.support.get('id')}
    }).done(function() {
      app_router.navigate('support', {trigger: true});
    });
    }else{
    	  enableButton(button); 
      }
  }



});


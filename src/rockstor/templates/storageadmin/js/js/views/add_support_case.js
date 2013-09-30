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
 * Add Support View 
 */

AddSupportCaseView = Backbone.View.extend({
  initialize: function() {
    this.support = new SupportCaseCollection();
  },
  render: function() {
    $(this.el).empty();
    this.template = window.JST.support_add_support_case_template;
    var _this = this;
    this.support.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({support: _this.support}));
        
        var raid_err_msg = function() {
            return err_msg;
          }
        
        $.validator.addMethod('validateSupportCaseName', function(value) {
            var support_notes = $('#support_notes').val();
            
           
            if (support_notes == "") {
                err_msg = 'Please enter Support Case name';
                return false;
                } 
            else
            if(support_notes.length >127){
                	err_msg = 'Please enter Support Case name less than 128 characters';
                	return false;
                	}
            
            
            return true;
          }, raid_err_msg);
        
        
        $('#add-support-case-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
          	  
            	support_notes: "validateSupportCaseName",  
          
           },
          
        submitHandler: function() {
            var support_notes = $('#support_notes').val();
                  
               $.ajax({
                 url: "/api/support",
                 type: "PUT",
                 dataType: "json",
                 data: {"type": "manual","notes":support_notes },
                 success: function() {
                    app_router.navigate('support', {trigger: true}) 
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
     }
   });


var addSupportCaseView = new AddSupportCaseView();

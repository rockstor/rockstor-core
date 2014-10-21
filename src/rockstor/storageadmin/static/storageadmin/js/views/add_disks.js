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

AddDiskView = RockstorLayoutView.extend({
  events: {
    'click #cancel': 'cancel'
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.disk_add_disks;
    this.disks = new DiskCollection();
    this.diskName = this.options.diskName;
    
  },
 render: function() {
    this.fetch(this.renderDisksForm, this);
    return this;
  },

  renderDisksForm: function() {
    var _this = this;
    var disk_name = this.diskName;
  	//var selectedDisk = this.disks.find(function(d){ return (d.get('name') == disk_name);});
  
    $(this.el).html(this.template({
    diskName: this.diskName,
    }));
   
     this.$('#add-disk-form :input').tooltip({
      html: true,
      placement: 'right'
    });
    
    $('#add-disk-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
       },
      
      submitHandler: function() {
      console.log("In submit handler");
      alert("in submit");
        var button = $('#add-disks');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var submitmethod = 'POST';
        var posturl = '/api/disks/' + this.diskName + '/blink-drive';
        $.ajax({
          url: posturl,
          type: submitmethod,
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(_this.$('#add-disk-form').getJSON()),
          success: function() {
           enableButton(button);
            _this.$('#add-disk-form :input').tooltip('hide');
            app_router.navigate('disks', {trigger: true});
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
    this.$('#add-disk-form :input').tooltip('hide');
    app_router.navigate('disks', {trigger: true});
  }

});

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

SmartcustomDiskView = RockstorLayoutView.extend({
  events: {
    'click #cancel': 'cancel'
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.disk_smartcustom_disks;
    this.disks = new DiskCollection();
    this.diskName = this.options.diskName;
    this.dependencies.push(this.disks);
  },

 render: function() {
    this.fetch(this.renderDisksForm, this);
    return this;
  },

  renderDisksForm: function() {
    if (this.$('[rel=tooltip]')) {
      this.$("[rel=tooltip]").tooltip('hide');
    }
    var _this = this;
    var disk_name = this.diskName;
    var serialNumber = this.disks.find(function(d){ return (d.get('name') == disk_name);}).get('serial');
    var currentSmartCustom = this.disks.find(function(d){ return (d.get('name') == disk_name);}).get('smart_options');

    $(this.el).html(this.template({
	diskName: this.diskName,
	serialNumber: serialNumber,
    currentSmartCustom: currentSmartCustom
    }));

    this.$('#add-smartcustom-disk-form :input').tooltip({
      html: true,
      placement: 'right'
    });

    var err_msg = '';
      var smartcustom_err_msg = function() {
          return err_msg;
      }

    $.validator.addMethod('validateSmartCustom', function(value) {
        var smartcustom_options = $('#smartcustom_options').val();
        if(smartcustom_options.length > 64){
            err_msg = 'S.M.A.R.T options length must not exceed 64 characters total';
            return false;
        }
        return true;
    }, smartcustom_err_msg);

    this.$('#add-smartcustom-disk-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
	  smartcustom_options: 'validateSmartCustom',
      },

      submitHandler: function() {
	    var button = $('#smartcustom-disk');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var submitmethod = 'POST';
        var posturl = '/api/disks/' + disk_name + '/smartcustom-drive';
        $.ajax({
          url: posturl,
          type: submitmethod,
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(_this.$('#add-smartcustom-disk-form').getJSON()),
          success: function() {
           enableButton(button);
            _this.$('#add-smartcustom-disk-form :input').tooltip('hide');
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
    this.$('#add-smartcustom-disk-form :input').tooltip('hide');
    app_router.navigate('disks', {trigger: true});
  }

});

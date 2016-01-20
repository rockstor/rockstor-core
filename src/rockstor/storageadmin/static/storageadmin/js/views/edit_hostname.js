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

EditHostnameView = RockstorLayoutView.extend({

  events: {
    'click #js-cancel': 'cancel'
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.appliances_edit_hostname;
    this.applianceId = this.options.applianceId;
  },

  render: function() {
    var _this = this;
    $(this.el).html(this.template());
    this.$('#edit-hostname-form :input').tooltip({
      html: true,
      placement: 'right'
    });
    this.$('#edit-hostname-form').validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        hostname: 'required',
        },
      submitHandler: function() {
        var button = _this.$('#edit-hostname');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var data = _this.$('#edit-hostname-form').getJSON();
        $.ajax({
          url: '/api/appliances/'+_this.applianceId,
          type: 'PUT',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(data),
          success: function() {
            _this.$('#edit-hostname-form :input').tooltip('hide');
            enableButton(button);
            app_router.navigate('appliances', {trigger: true});
          },
          error: function(xhr, status, error) {
            _this.$('#edit-hostname-form :input').tooltip('hide');
            enableButton(button);
          }
        });
      }
    });
    return this;
  },

  cancel: function(event) {
    event.preventDefault();
    app_router.navigate('appliances', {trigger: true});
  }

});

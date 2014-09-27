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

SMBShares  = RockstorModuleView.extend({
  events: {
    'click #add-smb-share': 'addSmbShare',
    'click #delete-smb-share': 'deleteSmbShare',
    'click #cancel-smb': 'cancelSmb',
  },

  initialize: function() {
    this.template = window.JST.share_smb_shares_template;
    this.smbAddTemplate = window.JST.share_smb_share_edit;
    this.module_name = 'smb_shares';
    this.share = this.options.share;
    this.smbShare = new SMBShare({shareName: this.share.get("name")});
    this.yes_no_choices = [
      {name: 'yes', value: 'yes'},
      {name: 'no', value: 'no'}, 
    ];
    this.browsable_choices = this.yes_no_choices;
    this.guest_ok_choices = this.yes_no_choices;
    this.read_only_choices = this.yes_no_choices;
  },

  render: function() {
    var _this = this;
    _this.$("#add-smb-form :input").tooltip('hide');
    $(this.el).empty();
    this.smbShare.fetch({
      success: function(model, response, options) {
        $(_this.el).append(_this.template({
          share: _this.share,
          smbShare: _this.smbShare,
          browsable_choices: _this.browsable_choices,
          guest_ok_choices: _this.guest_ok_choices,
          read_only_choices: _this.read_only_choices,
        }));
      },
      error: function(model, response, options) {
        console.log(response);
      }
    });
    return this;
  },

  addSmbShare: function(event) {
    var _this = this;
    event.preventDefault();
    $(this.el).html(this.smbAddTemplate({
      smbShare: this.smbShare,
      browsable_choices: this.browsable_choices,
      guest_ok_choices: this.guest_ok_choices,
      read_only_choices: this.read_only_choices,
    }));
    this.$("#add-smb-form :input").tooltip({
      html: true,
      placement: 'right',
    });
    this.$("#add-smb-form").validate({
      onfocusout: false,
      onkeyup: false,
      rules: {
        host_str: "required"
      },
      submitHandler: function() {
        var button = _this.$('#save-smb');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var data = {
          browsable: _this.$("#browsable").val(),
          guest_ok: _this.$("#guest_ok").val(),  
          read_only: _this.$("#read_only").val(),
          admin_users: _this.$('#admin_users').val(),
          comment: _this.$("#comment").val()
        };
        _this.smbShare.save(
          data,
          {
            success: function() {
              enableButton(button);
              _this.render();
            },
            error: function(model, xhr, options) {
              enableButton(button);
            },
          }
        );
        return false;
      }

    });
  },

  cancelSmb: function(event) {
    event.preventDefault();
    this.render();
  },

  deleteSmbShare: function(event) {
    var button = this.$('#delete');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    event.preventDefault();
    var _this = this;
    if (!_.isNull(this.smbShare)) {
      this.smbShare.destroy({
        success: function() {
          _this.smbShare = new SMBShare({shareName: _this.share.get("name")});
          enableButton(button);
          _this.render();
        },
        error: function(model, xhr, options) {
          enableButton(button);
          var msg = parseXhrError(xhr.responseText);
          _this.$(".messages").html(this.errTemplate({msg: msg}));
        },
      });
    }
  },
  
});

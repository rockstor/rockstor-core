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

SMBShares  = RockstoreModuleView.extend({
  events: {
    'click #add-smb-share': 'addSmbShare',
    'click #cancel-add': 'cancelAdd',
    'click #cancel-edit': 'cancelEdit',
    'click #create': 'create',
    'click #edit': 'edit',
    'click #delete': 'deleteSmbShare',
    'click #update': 'update',
  },

  initialize: function() {
    this.template = window.JST.share_smb_shares_template;
    this.module_name = 'smb_shares';
    this.share = this.options.share;
    this.smb_shares = new SMBShareCollection();
    this.smb_shares.reset(this.share.get('smb_shares'));
    this.smb_share = null;
    if (this.smb_shares.length > 0) {
      this.smb_share = this.smb_shares.at(0);
      this.smb_share.set({shareName: this.share.get('name')});
    }
    this.row_template = window.JST.share_smb_shares_table_row_template;
    this.add_row_template = window.JST.share_smb_shares_table_new_row_template;
    this.edit_row_template = window.JST.share_smb_shares_table_edit_row_template;
    this.empty_body_template = window.JST.share_smb_shares_table_empty_body_template;
    this.share.on('change', function() {
      this.smb_shares.reset(this.share.get('smb_shares'));
    }, this)
    this.yes_no_choices = [
      {name: 'yes', value: 'yes'},
      {name: 'no', value: 'no'}, 
    ];
    this.browsable_choices = this.yes_no_choices;
    this.guest_ok_choices = this.yes_no_choices;
    this.read_only_choices = this.yes_no_choices;
  },

  render: function() {
    console.log('smb_shares render called');
    var _this = this;
    $(this.el).empty();
    $(this.el).append(this.template({
      share: this.share,
      smb_shares: this.smb_shares,
      smb_share: this.smb_share,
      browsable_choices: this.browsable_choices,
      guest_ok_choices: this.guest_ok_choices,
      read_only_choices: this.read_only_choices,
    }));
    return this;
  },

  addSmbShare: function(event) {
    event.preventDefault();
    var button = $(event.currentTarget);
    if (!button.hasClass('disabled')) {
      if (this.smb_shares.length == 0) {
        this.$('#smb-shares-table-body').empty();
      }
      this.$('#smb-shares-table-body').append(this.add_row_template({
        browsable_choices: this.browsable_choices,
        guest_ok_choices: this.guest_ok_choices,
        read_only_choices: this.read_only_choices,

      }));
    }
    this.disableAddButton();

  },

  disableAddButton: function() {
    this.$('#add-smb-share').addClass('disabled');
  },
  
  enableAddButton: function() {
    this.$('#add-smb-share').removeClass('disabled');
  },

  cancelAdd: function(event) {
    event.preventDefault();
    this.$('#new-row').remove();
    this.enableAddButton();
    if (this.smb_shares.length == 0) {
      this.$('#smb-shares-table-body').append(this.empty_body_template());
    }
  },

  create: function(event) {
    event.preventDefault();
    var button = this.$('#create');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    var _this = this;
    data = {
      browsable: this.$('#browsable').val(),
      guest_ok: this.$('#guest_ok').val(),
      read_only: this.$('#read_only').val(),
      comment: this.$('#comment').val()
    }
    logger.info('saving with data');
    console.log(data);
    this.smb_share = new SMBShare({shareName: this.share.get('name')});
    this.smb_share.save(
      data,
      {
        success: function(model, response, options) {
          _this.render();
        },
        error: function(model, xhr, options) {
          enableButton(button);
          showError(xhr.responseText);
        }
      }
    );
  },

  cancelEdit: function(event) {
    event.preventDefault();
    this.$('#smb-shares-table-body').empty();
    this.$('#smb-shares-table-body').append(this.row_template({
      smb_share: this.smb_shares.at(0),
    }));
  },

  edit: function(event) {
    event.preventDefault();
    console.log('edit');
    this.$('#smb-shares-table-body').empty();
    this.$('#smb-shares-table-body').append(this.edit_row_template({
      browsable_choices: this.browsable_choices,
      guest_ok_choices: this.guest_ok_choices,
      read_only_choices: this.read_only_choices,
      smb_share: this.smb_shares.at(0),

    }));

  },

  deleteSmbShare: function(event) {
    var button = this.$('#delete');
    if (buttonDisabled(button)) return false;
    disableButton(button);
    event.preventDefault();
    var _this = this;
    if (!_.isNull(this.smb_share)) {
      console.log('calling smb_share destroy');
      this.smb_share.destroy({
        success: function() {
          console.log('destroyed smb_share successfully')
          _this.smb_share = null        
          _this.render();
        },
        error: function(request, status, error) {
          enableButton(button);
          showError(request.responseText);
        },
      });
    }
  },
  
  update: function(event) {
    event.preventDefault();
    var _this = this;
    data = this.$('#smb-row').getJSON();
    console.log(data);
    $.ajax({
      url: "/api/shares/"+_this.share.get('name')+'/smb-update/',
      type: "PUT",
      dataType: "json",
      data: data,
      success: function() {
        _this.render();
      },
      error: function(request, status, error) {
        showError(request.responseText);
      },
    });

  },



  
});

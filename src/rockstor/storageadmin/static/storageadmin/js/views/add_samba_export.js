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

AddSambaExportView = RockstorLayoutView.extend({
    events: {
	'click #cancel': 'cancel',
	'click #shadow-copy-info': 'shadowCopyInfo',
	'click #shadow_copy': 'toggleSnapPrefix'
    },

    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.samba_add_samba_export;
	this.shares = new ShareCollection();
	this.users = new UserCollection();
	// dont paginate shares for now
	this.shares.pageSize = RockStorGlobals.maxPageSize;
	this.users.pageSize = RockStorGlobals.maxPageSize;
	this.dependencies.push(this.shares);
	this.dependencies.push(this.users);
	this.sambaShareId = this.options.sambaShareId;
	this.sambaShares = new SambaCollection({sambaShareId: this.sambaShareId});
	this.dependencies.push(this.sambaShares);

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
	this.freeShares = this.shares.reject(function(share) {
	    s = this.sambaShares.find(function(sambaShare) {
		return (sambaShare.get('share') == share.get('name'));
	    });
	    return !_.isUndefined(s);
	}, this);

	this.sShares = this.shares.reject(function(share) {
	    s = this.sambaShares.find(function(sambaShare) {
		return (sambaShare.get('share') != share.get('name'));
	    });
	    return !_.isUndefined(s);
	}, this);

	if(this.sambaShareId != null){
	    this.sShares = this.sambaShares.get(this.sambaShareId);
        }else{
	    this.sShares = null;
	}

	var configList = '';
	if (this.sShares != null) {
            var config = this.sShares.get('custom_config');
            for(i=0;i<config.length;i++){
		configList = configList+config[i].custom_config+'\n';
            }
	}

	$(this.el).html(this.template({
	    shares: this.freeShares,
	    smbShare: this.sShares,
	    users: this.users,
	    configList: configList,
	    sambaShareId: this.sambaShareId,
	    browsable_choices: this.browsable_choices,
	    guest_ok_choices: this.guest_ok_choices,
	    read_only_choices: this.read_only_choices,
	    shadow_copy_choices: this.yes_no_choices

	}));
	if(this.sambaShareId == null) {
	    this.$('#shares').chosen();
	}
	this.$('#admin_users').chosen();

	this.$('#add-samba-export-form :input').tooltip({
	    html: true,
	    placement: 'right'
	});

	$.validator.setDefaults({ ignore: ":hidden:not(select)" });

	$('#add-samba-export-form').validate({
	    onfocusout: false,
	    onkeyup: false,
	    rules: {
		shares: 'required',
		snapshot_prefix: {
		    required: {
			depends: function(element) {
			    return _this.$('#shadow_copy').prop('checked');
			}
		    }
		}
	    },

	    submitHandler: function() {
		var button = $('#create-samba-export');
		var custom_config = _this.$('#custom_config').val();
		var entries = [];
		if (!_.isNull(custom_config) && custom_config.trim() != '') entries = custom_config.trim().split('\n');
		if (buttonDisabled(button)) return false;
		disableButton(button);
		var submitmethod = 'POST';
		var posturl = '/api/samba';
		if(_this.sambaShareId != null){
		    submitmethod = 'PUT';
		    posturl += '/'+_this.sambaShareId;
		}
		var data = _this.$('#add-samba-export-form').getJSON();
		data.custom_config = entries;
		$.ajax({
		    url: posturl,
		    type: submitmethod,
		    dataType: 'json',
		    contentType: 'application/json',
		    data: JSON.stringify(data),
		    success: function() {
			enableButton(button);
			_this.$('#add-samba-export-form :input').tooltip('hide');
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
	this.$('#add-samba-export-form :input').tooltip('hide');
	app_router.navigate('samba-exports', {trigger: true});
    },

    shadowCopyInfo: function(event) {
	var _this = this;
	event.preventDefault();
	console.log('hello');
	$('#shadow-copy-info-modal').modal({
	    keyboard: false,
	    show: false,
	    backdrop: 'static'
	});
	$('#shadow-copy-info-modal').modal('show');
    },

    toggleSnapPrefix: function() {
	var cbox = this.$('#shadow_copy');
	if (cbox.prop('checked')) {
	    this.$('#snapprefix-ph').css('visibility', 'visible');
	} else {
	    this.$('#snapprefix-ph').css('visibility', 'hidden');
	}
    }

});

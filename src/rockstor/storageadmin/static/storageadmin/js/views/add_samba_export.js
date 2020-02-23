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
        'click #time-machine-info': 'TimeMachineInfo',
        'click #shadow_copy': 'toggleSnapPrefix',
        'click .mutually-exclusive': 'disableBoxes'
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
        this.sambaShareId = this.options.sambaShareId || null;
        this.sambaShares = new SambaCollection({sambaShareId: this.sambaShareId});
        this.dependencies.push(this.sambaShares);

        this.yes_no_choices = [
            {name: 'yes', value: 'yes'},
            {name: 'no', value: 'no'},
        ];
        this.initHandlebarHelpers();
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
        //convert array elements into JSON objects
        for(var i = 0; i < this.freeShares.length; i++){
            this.freeShares[i] = this.freeShares[i].toJSON();
        }

        this.sShares = this.shares.reject(function(share) {
            s = this.sambaShares.find(function(sambaShare) {
                return (sambaShare.get('share') != share.get('name'));
            });
            return !_.isUndefined(s);
        }, this);

        //Edit view gets the sambaShareId from initalize function and Null in Add view.
        var sambaShareIdNotNull = false;
        var sambaShareIdNull = false;

        if(this.sambaShareId == null){
            sambaShareIdNull = true;
        }
        if(this.sambaShareId != null){
            this.sShares = this.sambaShares.get(this.sambaShareId);
            sambaShareIdNotNull = true;
        }else{
            this.sShares = null;
        }

        var configList = '',
            smbShareName,
            smbShadowCopy,
            smbTimeMachine,
            smbComment,
            smbSnapPrefix = '';
        if (this.sShares != null) {
            var config = this.sShares.get('custom_config');
            smbShareName = this.sShares.get('share');
            smbShadowCopy = this.sShares.get('shadow_copy');
            smbTimeMachine = this.sShares.get('time_machine');
            smbComment = this.sShares.get('comment');
            smbSnapPrefix = this.sShares.get('snapshot_prefix');

            for(i=0; i<config.length; i++){
                configList = configList + config[i].custom_config;
                configList += i<config.length - 1 ? '\n' : '';
            }
        }


        var smbSnapshotPrefixBool = false;
        if(sambaShareIdNotNull && smbShadowCopy){
            smbSnapshotPrefixBool = true;
        }
        $(this.el).html(this.template({
            shares: this.freeShares,
            smbShare: this.sShares,
            smbShareName: smbShareName,
            smbShareShadowCopy: smbShadowCopy,
            smbShareTimeMachine: smbTimeMachine,
            smbShareComment: smbComment,
            smbShareSnapPrefix: smbSnapPrefix,
            smbSnapshotPrefixRule: smbSnapshotPrefixBool,
            users: this.users,
            configList: configList,
            sambaShareId: this.sambaShareId,
            sambaShareIdNull: sambaShareIdNull,
            sambaShareIdNotNull: sambaShareIdNotNull,
            yes_no_choices: this.yes_no_choices,

        }));
        if(this.sambaShareId == null) {
            this.$('#shares').select2();
        }
        this.$('#admin_users').select2();
        this.$('#add-samba-export-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        $.validator.setDefaults({ ignore: ':hidden:not(select)' });

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
        event.preventDefault();
        $('#shadow-copy-info-modal').modal({
            keyboard: false,
            show: false,
            backdrop: 'static'
        });
        $('#shadow-copy-info-modal').modal('show');
    },

    TimeMachineInfo: function(event) {
        event.preventDefault();
        $('#time-machine-info-modal').modal({
            keyboard: false,
            show: false,
            backdrop: 'static'
        });
        $('#time-machine-info-modal').modal('show');
    },

    toggleSnapPrefix: function() {
        var cbox = this.$('#shadow_copy');
        if (cbox.prop('checked')) {
            this.$('#snapprefix-ph').css('visibility', 'visible');
        } else {
            this.$('#snapprefix-ph').css('visibility', 'hidden');
        }
    },

    disableBoxes: function() {
        if (this.$('#shadow_copy').attr('checked')) {
            this.$('#time_machine').attr('disabled', true);
        } else if (this.$('#time_machine').attr('checked')) {
            this.$('#shadow_copy').attr('disabled', true);
        } else {
            this.$('.mutually-exclusive').attr('disabled', false);
        }
    },

    initHandlebarHelpers: function(){
        Handlebars.registerHelper('display_adminUser_options', function(){
            var html = '';
            var _this = this;
            this.users.each(function(user, index) {
                var userName = user.get('username');
                html += '<option value="' + userName + '"';
                if (_this.sambaShareIdNotNull && _this.smbShare.get('admin_users').length > 0) {
                    for(i=0; i< _this.smbShare.get('admin_users').length; i++){
                        if(_this.smbShare.get('admin_users')[i].username == userName){
                            html += 'selected= "selected"';
                        }
                    }

                }
                html += '>' + userName + '</option>';
            });

            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_options', function(inputOption){
            var html = '';
            var _this = this;
            _.each(this.yes_no_choices, function(c) {
                var choiceValue = c.value,
                    choiceName = c.name;

                html += '<label class="radio-inline"><input type="radio" name="'+ inputOption + '" value="' + choiceValue + '"';

                if (_this.sambaShareIdNotNull){ //edit samba export functionality
                    if(choiceValue == _this.smbShare.get(inputOption)){
                        html += 'checked';
                    }
                }else { // add export functionality
                    if(inputOption == 'browsable'){
                        if(choiceValue == 'yes'){
                            html += 'checked';
                        }
                    }else if(choiceValue == 'no'){ // when the inputOptions are 'guest_ok' and 'read_only' default value is 'NO'
                        html += 'checked';
                    }
                }
                html += '>' + choiceName + '</label>';
            });

            return new Handlebars.SafeString(html);
        });
    }

});

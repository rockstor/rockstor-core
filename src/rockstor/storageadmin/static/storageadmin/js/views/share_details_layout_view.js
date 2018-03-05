/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
ShareDetailsLayoutView = RockstorLayoutView.extend({
    id: 'share-details-container',
    events: {
        'click #js-acl-edit': 'editAcl',
        'click #js-acl-save': 'saveAcl',
        'click #js-acl-cancel': 'cancelAcl',
        'click input[name=\'perms[]\']': 'showPermStr',
        'click #js-edit-compression': 'editCompression',
        'click #js-edit-compression-cancel': 'editCompressionCancel',
        'click #js-submit-compression': 'updateCompression',
        'click #js-delete': 'deleteShare',
        'click #js-cancel': 'cancel',
        'click #js-confirm-share-delete': 'confirmShareDelete'
    },

    initialize: function() {
        // call initialize of base
        this.constructor.__super__.initialize.apply(this, arguments);
        this.shareId = this.options.shareId;
        this.template = window.JST.share_share_details_layout;
        this.rollback_btn_template = window.JST.share_share_details_rollback_btn;
        this.shareAclTemplate = window.JST.share_share_acl;
        this.shareAclEditTemplate = window.JST.share_share_acl_edit;
        this.compression_info_template = window.JST.share_compression_info;
        this.compression_info_edit_template = window.JST.share_compression_info_edit;
        this.appliances = new ApplianceCollection();
        this.appliances.pageSize = RockStorGlobals.maxPageSize;

        // create models
        this.share = new Share({
            sid: this.shareId
        });
        this.snapshots = new SnapshotCollection([]);
        this.snapshots.setUrl(this.shareId);

        this.users = new UserCollection();
        this.users.pageSize = RockStorGlobals.maxPageSize;
        this.groups = new GroupCollection();
        this.groups.pageSize = RockStorGlobals.maxPageSize;
        // add dependencies
        this.dependencies.push(this.share);
        this.dependencies.push(this.snapshots);
        this.dependencies.push(this.users);
        this.dependencies.push(this.groups);
        this.dependencies.push(this.appliances);
        this.modify_choices = [{
            name: 'ro',
            value: 'ro'
        },
        {
            name: 'rw',
            value: 'rw'
        },
        ];
        this.sync_choices = [{
            name: 'async',
            value: 'async'
        },
        {
            name: 'sync',
            value: 'sync'
        },
        ];
        this.nsecurity_choices = [{
            name: 'secure',
            value: 'secure'
        },
        {
            name: 'insecure',
            value: 'insecure'
        },
        ];
        this.on('snapshotsModified', this.renderRollbackBtn, this);
        this.cOpts = {
            'no': 'Dont enable compression',
            'zlib': 'zlib',
            'lzo': 'lzo'
        };
        this.cView = this.options.cView;
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderSubViews, this);
        return this;
    },

    renderSubViews: function() {
        var current_appliance = this.appliances.find(function(appliance) {
            return appliance.get('current_appliance') == true;
        });
        var systemShare = false;
        if (parseInt(this.share.get('id')) < 3 && this.share.get('pool')['role'] == 'root') {
            systemShare = true;
        }
        this.subviews['share-usage'] = new ShareUsageModule({
            share: this.share
        });
        this.subviews['snapshots'] = new SnapshotsTableModule({
            snapshots: this.snapshots,
            share: this.share,
            parentView: this
        });
        this.share.on('change', this.subviews['share-usage'].render, this.subviews['share-usage']);
        $(this.el).html(this.template({
            share: this.share,
            shareName: this.share.get('name'),
            shareId: this.share.get('id'),
            shareUsage: humanize.filesize(this.share.get('rusage') * 1024),
            snapshots: this.snapshots,
            permStr: this.parsePermStr(this.share.get('perms')),
            modify_choices: this.modify_choices,
            sync_choices: this.sync_choices,
            nsecurity_choices: this.nsecurity_choices,
            isSystemShare: systemShare
        }));
        this.renderRollbackBtn();
        this.renderAcl();
        this.$('#ph-share-usage').html(this.subviews['share-usage'].render().el);
        this.$('#ph-snapshots').html(this.subviews['snapshots'].render().el);
        this.shareCompressBool = false;
        if (_.isNull(this.share.get('compression_algo')) || this.share.get('compression_algo') == 'no') {
            this.shareCompressBool = true;
        }
        if (!_.isUndefined(this.cView) && this.cView == 'edit') {
            this.$('#ph-compression-info').html(this.compression_info_edit_template({
                share: this.share,
                cOpts: this.cOpts
            }));
            this.showCompressionTooltips();
        } else {
            this.$('#ph-compression-info').html(this.compression_info_template({
                share: this.share,
                shareCompression: this.share.get('compression_algo'),
                shareCompressionNull: this.shareCompressBool
            }));
        }
        this.$('ul.nav.nav-tabs').tabs('div.css-panes > div');
        this.attachActions();
    },

    renderRollbackBtn: function() {
        var foundWritableSnapshot,
            rollbackBtnDisabler = false;
        if (!_.isUndefined(this.snapshots.find(function(s) {
            return s.get('writable') == true;
        }))) {
            foundWritableSnapshot = true;
        }
        if (this.snapshots.isEmpty() || !foundWritableSnapshot) {
            rollbackBtnDisabler = true;
        }
        this.$('#rollback-btn-ph').html(this.rollback_btn_template({
            foundWritableSnapshot: foundWritableSnapshot,
            shareId: this.share.get('id'),
            rollbackBtnDisabler: rollbackBtnDisabler
        }));

    },

    attachActions: function() {
        var _this = this;
        // attach overlays
        this.$('#js-access-control').overlay();
        // create snapshot form submit action
        this.$('#create-snapshot').click(function() {
            var button = _this.$('#create-snapshot');
            if (buttonDisabled(button)) return false;
            disableButton(button);
            $.ajax({
                url: '/api/shares/' + _this.share.get('id') + '/snapshots/' + $('#snapshot-name').val(),
                type: 'POST',
                dataType: 'json'
            }).done(function() {
                enableButton(button);
                _this.$('#js-snapshot-popup').overlay().close();
                _this.snapshots.fetch();
                //_this.$('#snapshots').empty().append(_this.snapshotsTableView.render().el);
            }).fail(function() {
                enableButton(button);
            });
        });
    },

    deleteShare: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        // show modal
        _this.$('#delete-share-modal').modal();
        return false;
    },

    confirmShareDelete: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var url = '/api/shares/' + _this.share.get('id');
        if ($('#force-delete').prop('checked')) {
            url += '/force';
        }
        $.ajax({
            url: url,
            type: 'DELETE',
            dataType: 'json',
            success: function() {
                enableButton(button);
                _this.$('#delete-share-modal').modal('hide');
                $('.modal-backdrop').remove();
                app_router.navigate('shares', {
                    trigger: true
                });
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    cancel: function(event) {
        if (event) event.preventDefault();
        app_router.navigate('shares', {
            trigger: true
        });
    },

    renderAcl: function() {
        this.$('#ph-access-control').html(this.shareAclTemplate({
            share: this.share,
            shareOwner: this.share.get('owner'),
            shareGroup: this.share.get('group'),
            sharePerms: this.share.get('perms'),
            permStr: this.parsePermStr(this.share.get('perms'))
        }));
    },

    editAcl: function(event) {
        event.preventDefault();
        this.$('#ph-access-control').html(this.shareAclEditTemplate({
            share: this.share.toJSON(),
            permStr: this.parsePermStr(this.share.get('perms')),
            users: this.users.toJSON(),
            groups: this.groups.toJSON(),
            sharePerms: this.share.get('perms')
        }));
    },

    saveAcl: function(event) {
        event.preventDefault();
        var _this = this;
        var button = _this.$('#js-acl-save');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var permStr = this.createPermStr();
        var data = {
            owner: this.$('#share-owner').val(),
            group: this.$('#share-group').val(),
            perms: permStr
        };
        $.ajax({
            url: '/api/shares/' + this.share.get('id') + '/acl',
            type: 'POST',
            data: data,
            dataType: 'json',
            success: function() {
                enableButton(button);
                _this.share.fetch({
                    success: function() {
                        _this.renderAcl();
                    }
                });
            },
            error: function(request, status, error) {
                enableButton(button);
            }
        });
    },

    cancelAcl: function(event) {
        event.preventDefault();
        this.$('#ph-access-control').html(this.shareAclTemplate({
            share: this.share,
            permStr: this.parsePermStr(this.share.get('perms'))
        }));
    },

    parsePermStr: function(perms) {
        var p = '';
        for (var i = 0; i < 3; i++) {
            var tmp = parseInt(perms.charAt(i)).toString(2);
            p = (tmp.length == 3) ? p.concat(tmp) :
                (tmp.length == 2) ? p.concat('0').concat(tmp) :
                p.concat('00').concat(tmp);
        }
        return p;
    },

    createPermStr: function() {
        var perms = [];
        this.$('input[name=\'perms[]\']:checked').each(function() {
            perms.push($(this).val());
        });
        var us = ['owner', 'group', 'other'];
        var ps = ['r', 'w', 'x'];
        var permStr = '';
        _.each(us, function(u) {
            var t = '';
            _.each(ps, function(p) {
                var s = u + '-' + p;
                t = t + (perms.indexOf(s) != -1 ? '1' : '0');
            });
            permStr = permStr + parseInt(t, 2);
        });
        return permStr;
    },

    showPermStr: function() {
        this.$('#permStrEdit').html(this.createPermStr());
    },

    showCompressionTooltips: function() {
        this.$('#ph-compression-info #compression').tooltip({
            html: true,
            placement: 'top',
            title: 'Choose a compression algorithm for this Share. By default, parent pool\'s compression algorithm is applied.<br> If you like to set pool wide compression, don\'t choose anything here. If you want finer control of this particular Share\'s compression algorithm, you can set it here.<br><strong>zlib: </strong>slower than lzo but higher compression ratio.<br><strong>lzo: </strong>faster than zlib but lower compression ratio.'
        });
    },

    hideCompressionTooltips: function() {
        this.$('#ph-compression-info #compression').tooltip('hide');
    },

    editCompression: function(event) {
        event.preventDefault();
        this.$('#ph-compression-info').html(this.compression_info_edit_template({
            share: this.share,
            cOpts: this.cOpts
        }));
        this.showCompressionTooltips();
    },

    editCompressionCancel: function(event) {
        event.preventDefault();
        this.hideCompressionTooltips();
        this.$('#ph-compression-info').html(this.compression_info_template({
            share: this.share,
            shareCompression: this.share.get('compression_algo'),
            shareCompressionNull: this.shareCompressBool
        }));
    },

    updateCompression: function(event) {
        var _this = this;
        event.preventDefault();
        var button = this.$('#js-submit-compression');
        if (buttonDisabled(button)) return false;
        disableButton(button);
        $.ajax({
            url: '/api/shares/' + this.share.get('id'),
            type: 'PUT',
            dataType: 'json',
            data: {
                'compression': this.$('#compression').val()
            },
            success: function() {
                _this.hideCompressionTooltips();
                _this.share.fetch({
                    success: function(collection, response, options) {
                        _this.cView = 'view';
                        _this.renderSubViews();
                    }
                });
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_share_compressOptions', function() {
            var html = '',
                _this = this;
            _.each(_.keys(_this.cOpts), function(c) {
                if (_this.share.get('compression_algo') == c) {
                    html += '<option value="' + c + '" selected="selected">' + _this.cOpts[c] + '</option>';
                } else {
                    html += '<option value="' + c + '">' + _this.cOpts[c] + '</option>';
                }
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('view_read_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[0] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[3] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[6] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('view_write_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[1] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[4] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[7] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('view_execute_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[2] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[5] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[8] == '1') {
                html += '<input type="checkbox" checked="true" disabled>';
            } else {
                html += '<input type="checkbox" disabled>';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });


        Handlebars.registerHelper('showOwnerOption', function(userName, shareOwner) {
            if (userName == shareOwner) {
                return 'selected = "selected"';
            }
        });

        Handlebars.registerHelper('showGroupOption', function(groupName, shareGroup) {
            if (groupName == shareGroup) {
                return 'selected = "selected"';
            }
        });

        Handlebars.registerHelper('edit_read_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[0] == '1') {
                html += '<input type="checkbox" name="perms[]" value="owner-r" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="owner-r">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[3] == '1') {
                html += '<input type="checkbox" name="perms[]" value="group-r" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="group-r">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[6] == '1') {
                html += '<input type="checkbox" name="perms[]" value="other-r" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="other-r">';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('edit_write_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[1] == '1') {
                html += '<input type="checkbox" name="perms[]" value="owner-w" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="owner-w">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[4] == '1') {
                html += '<input type="checkbox" name="perms[]" value="group-w" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="group-w">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[7] == '1') {
                html += '<input type="checkbox" name="perms[]" value="other-w" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="other-w">';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('edit_execute_permissions', function() {
            var html = '';
            html += '<td>';
            if (this.permStr[2] == '1') {
                html += '<input type="checkbox" name="perms[]" value="owner-x" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="owner-x">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[5] == '1') {
                html += '<input type="checkbox" name="perms[]" value="group-x" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="group-x">';
            }
            html += '</td>';
            html += '<td>';
            if (this.permStr[8] == '1') {
                html += '<input type="checkbox" name="perms[]" value="other-x" checked="true">';
            } else {
                html += '<input type="checkbox" name="perms[]" value="other-x">';
            }
            html += '</td>';
            return new Handlebars.SafeString(html);
        });
    }

});

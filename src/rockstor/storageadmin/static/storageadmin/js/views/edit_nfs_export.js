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

EditNFSExportView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.nfs_edit_nfs_export;
        this.shares = new ShareCollection();
        this.nfsExportGroupId = this.options.nfsExportGroupId;
        if (this.nfsExportGroupId > 0) {
            this.nfsExportGroup = new NFSExportGroup({
                id: this.nfsExportGroupId
            });
            this.nfsExportNotEmpty = true;
            this.dependencies.push(this.nfsExportGroup);
        } else {
            this.nfsExportGroup = new NFSExportGroup();
        }
        // dont paginate shares for now
        this.shares.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.shares);
        this.modify_choices = [{
            name: 'Writable',
            value: 'rw'
        },
        {
            name: 'Read only',
            value: 'ro'
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
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderExportForm, this);
        return this;
    },

    renderExportForm: function() {
        var _this = this;
        $(this.el).html(this.template({
            shares: this.shares.toJSON(),
            nfsExportGrp: this.nfsExportGroup.toJSON(),
            nfsExportNotEmpty: this.nfsExportNotEmpty,
            modify_choices: this.modify_choices,
            sync_choices: this.sync_choices
        }));
        this.$('#shares').select2();
        this.$('#edit-nfs-export-form :input').tooltip({
            placement: 'right'
        });

        $.validator.setDefaults({
            ignore: ':hidden:not(select)'
        });

        this.$('#edit-nfs-export-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                shares: 'required',
                host_str: 'required'
            },
            submitHandler: function() {
                var button = $('#update-nfs-export');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/nfs-exports';
                if (_this.nfsExportGroupId > 0) {
                    submitmethod = 'PUT';
                    posturl += '/' + _this.nfsExportGroupId;
                }
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#edit-nfs-export-form').getJSON()),
                    success: function() {
                        app_router.navigate('nfs-exports', {
                            trigger: true
                        });
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
        app_router.navigate('nfs-exports', {
            trigger: true
        });
    },


    initHandlebarHelpers: function() {
        var _this = this;
        Handlebars.registerHelper('showSelectedShare', function(shareName, nfsExports) {
            var html = '',
                nShares = _.map(nfsExports,
                    function(e) {
                        return e.share;
                    });

            if (_.indexOf(nShares, shareName) != -1) {
                html += 'selected="selected"';
            }

            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('accessType_editView', function(nfsEditable, choiceValue) {
            var html = '';
            if (nfsEditable == choiceValue) {
                html += 'checked="checked"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('accessType_addView', function(choiceName) {
            var html = '';
            if (choiceName == 'Writable') {
                html += 'checked="checked"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('responseType_editView', function(nfsSyncable, choiceValue) {
            var html = '';
            if (nfsSyncable == choiceValue) {
                html += 'checked="checked"';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('responseType_addView', function(choiceName) {
            var html = '';
            if (choiceName == 'async') {
                html += 'checked="checked"';
            }
            return new Handlebars.SafeString(html);
        });
    }

});
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
SnapshotsView = SnapshotsCommonView.extend({
    events: {
        'click #js-snapshot-add': 'add',
        'click #js-snapshot-cancel': 'cancel',
        'click .js-snapshot-delete': 'deleteSnapshot',
        'click .js-snapshot-clone': 'cloneSnapshot',
        'click .js-snapshot-select': 'selectSnapshot',
        'click .js-snapshot-select-all': 'selectAllSnapshots',
        'click #js-snapshot-delete-multiple': 'deleteMultipleSnapshots'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.share_snapshots;
        this.addTemplate = window.JST.share_snapshot_add_template;
        this.module_name = 'snapshots';
        this.snapshots = this.options.snapshots;
        this.collection = new SnapshotsCollection();
        this.shares = new ShareCollection();
        this.dependencies.push(this.shares);
        this.dependencies.push(this.collection);
        this.selectedSnapshots = [];
        this.replicaShareMap = {};
        this.snapShares = [];

        this.modify_choices = [{
            name: 'yes',
            value: 'yes'
        },
        {
            name: 'no',
            value: 'no'
        },
        ];
        this.parentView = this.options.parentView;
        this.collection.on('reset', this.renderSnapshots, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderSnapshots, this);
        return this;
    },


    renderSnapshots: function() {
        var _this = this;
        $(this.el).empty();

        var snapshots = _this.collection.toJSON();
        for (var i = 0; i < snapshots.length; i++) {
            var shareMatch = _this.shares.find(function(share) {
                return share.get('id') == snapshots[i].share;
            });
            snapshots[i].share_name = shareMatch.get('name');
            snapshots[i].share_is_mounted = shareMatch.get('is_mounted');
            snapshots[i].share_mount_status = shareMatch.get('mount_status');
        }
        $(this.el).append(_this.template({
            snapshots: snapshots,
            snapshotsNotEmpty: !_this.collection.isEmpty(),
            collection: _this.collection
        }));

        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });

        var customs = {
            columnDefs: [
                { type: 'file-size', targets: 2 },
                { type: 'file-size', targets: 3 }
            ]
        };

        this.renderDataTables(customs);

        return this;
    },

    // may be redundant
    setShareName: function(shareName) {
        this.collection.setUrl(shareName);
    },

    // it may be this method is redundant if, instead, we retrieve share id
    // via added template attribute data-share-id sourced from snapshots array
    // and move to shareID as value in share drop down (snapshot_add_template).
    // See other TODOs in this file.
    getShareId: function(shareName) {
        var shareMatch = this.shares.find(function(share) {
            return share.get('name') == shareName;
        });
        return shareMatch.get('id');
    },

    add: function(event) {
        var _this = this;
        event.preventDefault();
        $(this.el).html(this.addTemplate({
            snapshots: this.collection
        }));
        this.$('#shares').select2();
        var err_msg = '';
        var name_err_msg = function() {
            return err_msg;
        };

        $.validator.addMethod('validateSnapshotName', function(value) {
            var snapshot_name = $('#snapshot_name').val();
            if (/^[A-Za-z0-9_.-]+$/.test(snapshot_name) == false) {
                err_msg = 'Please enter a valid snapshot name.';
                return false;
            }
            return true;
        }, name_err_msg);

        this.$('#add-snapshot-form :input').tooltip({
            placement: 'right'
        });
        this.validator = this.$('#add-snapshot-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                snapshot_name: 'validateSnapshotName',
                shares: 'required'
            },
            submitHandler: function() {
                var button = _this.$('#js-snapshot-save');
                // TODO: if handlebars helper show_shares_dropdown moves to
                // passing value of shareId then the following line could be:
                // var shareId = $('#shares').val();
                // making the existing shareID def redundant and removes the
                // need to call getShareID: assuming shareName is not needed.
                var shareName = $('#shares').val();
                var shareId = _this.getShareId(shareName);
                if (buttonDisabled(button)) return false;
                disableButton(button);
                $.ajax({
                    url: '/api/shares/' + shareId + '/snapshots/' + _this.$('#snapshot_name').val(),
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-snapshot-form').getJSON()),
                    success: function() {
                        _this.$('#add-snapshot-form :input').tooltip('hide');
                        enableButton(button);
                        _this.collection.fetch({
                            success: function(collection, response, options) {}
                        });
                    },
                    error: function(xhr, status, error) {
                        _this.$('#add-snapshot-form :input').tooltip('hide');
                        enableButton(button);
                    }
                });

                return false;
            }
        });
    },

    deleteSnapshot: function(event) {
        event.preventDefault();
        var _this = this;
        var name = $(event.currentTarget).attr('data-name');
        var shareName = $(event.currentTarget).attr('data-share-name');
        // TODO: consider moving next line to:
        // var shareId = $(event.currentTarget).attr('data-share-id');
        var shareId = _this.getShareId(shareName);
        var esize = $(event.currentTarget).attr('data-size');
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        if (confirm('Deleting snapshot(' + name + ') deletes ' + esize + ' of data permanently. Do you really want to delete it?')) {
            disableButton(button);
            $.ajax({
                url: '/api/shares/' + shareId + '/snapshots/' + name,
                type: 'DELETE',
                success: function() {
                    enableButton(button);
                    _this.$('[rel=tooltip]').tooltip('hide');
                    _this.selectedSnapshots = [];
                    _this.collection.fetch({
                        reset: true
                    });

                },
                error: function(xhr, status, error) {
                    enableButton(button);
                    _this.$('[rel=tooltip]').tooltip('hide');
                }
            });
        }
    },

    cloneSnapshot: function(event) {
        if (event) event.preventDefault();
        // Remove current tooltips to prevent them hanging around
        // even after new page has loaded.
        this.$('[rel=tooltip]').tooltip('hide');
        var name = $(event.currentTarget).attr('data-name');
        var shareName = $(event.currentTarget).attr('data-share-name');
        // TODO: consider moving next line to:
        // var shareId = $(event.currentTarget).attr('data-share-id');
        var shareId = this.getShareId(shareName);
        var url = 'shares/' + shareId + '/snapshots/' +
            name + '/create-clone';
        app_router.navigate(url, {
            trigger: true
        });

    },

    deleteMultipleSnapshots: function(event) {
        var _this = this;
        event.preventDefault();
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        if (this.selectedSnapshots.length == 0) {
            alert('Select at least one snapshot to delete');
        } else {
            var confirmMsg = null;
            if (this.selectedSnapshots.length == 1) {
                confirmMsg = 'Deleting snapshot ';
            } else {
                confirmMsg = 'Deleting snapshots ';
            }
            var snapNames = _.reduce(this.selectedSnapshots, function(str, snap) {
                return str + snap.get('name') + ',';
            }, '', this);
            snapNames = snapNames.slice(0, snapNames.length - 1);

            var snapIds = _.reduce(this.selectedSnapshots, function(str, snap) {
                return str + snap.id + ',';
            }, '', this);
            snapIds = snapIds.slice(0, snapIds.length - 1);

            var totalSize = _.reduce(this.selectedSnapshots, function(sum, snap) {
                return sum + snap.get('eusage');
            }, 0, this);

            var totalSizeStr = humanize.filesize(totalSize * 1024);

            if (confirm(confirmMsg + snapNames + ' deletes ' + totalSizeStr + ' of data. Are you sure?')) {
                disableButton(button);

                _.each(this.selectedSnapshots, function(s) {
                    var name = s.get('name');

                    _this.shares.each(function(share, index) {
                        if (s.get('share') == share.get('id')) {
                            var shareId = share.get('id');
                            $.ajax({
                                url: '/api/shares/' + shareId + '/snapshots/' + name,
                                type: 'DELETE',
                                success: function() {
                                    enableButton(button);
                                    _this.$('[rel=tooltip]').tooltip('hide');
                                    _this.selectedSnapshots = [];
                                    _this.collection.fetch({
                                        reset: true
                                    });

                                },
                                error: function(xhr, status, error) {
                                    enableButton(button);
                                    _this.$('[rel=tooltip]').tooltip('hide');
                                }
                            });

                        }
                    });
                });
            }
        }
    },

    selectedContains: function(name) {
        return _.find(this.selectedSnapshots, function(snap) {
            return snap.get('name') == name;
        });
    },

    addToSelected: function(name) {
        this.selectedSnapshots.push(this.collection.find(function(snap) {
            return snap.get('name') == name;
        }));
    },

    removeFromSelected: function(name) {
        var i = _.indexOf(_.map(this.selectedSnapshots, function(snap) {
            return snap.get('name');
        }), name);
        this.selectedSnapshots.splice(i, 1);
    },

    cancel: function(event) {
        event.preventDefault();
        this.render();
    },

    initHandlebarHelpers: function() {
        var _this = this;
        Handlebars.registerHelper('checkboxValue', function(snapName) {
            var html = '';
            if (RockstorUtil.listContains(_this.selectedSnapshots, 'name', snapName)) {
                html += 'checked="checked"';
            } else {
                html += '';
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('getToc', function(toc) {
            return moment(toc).format(RS_DATE_FORMAT);
        });

        Handlebars.registerHelper('getSize', function(size) {
            return humanize.filesize(size * 1024);
        });

        //Create Snapshot Template Helpers
        Handlebars.registerHelper('show_shares_dropdown', function() {
            var html = '';
            _this.shares.each(function(share, index) {
                var shareName = share.get('name');
                // var shareId = share.get('id');
                // TODO: consider above shareId as value: avoids getShareId() use.
                html += '<option value="' + shareName + '">' + shareName + '</option>';
            });
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_writeable_options', function() {
            var html = '';
            _.each(_this.modify_choices, function(c) {
                html += '<label class="radio-inline">';
                if (c.value == 'yes') {
                    html += '<input type="radio" name="writable" value="rw" checked>' + c.name;
                } else {
                    html += '<input type="radio" name="writable" value="ro" title="Note that (1)read-only snapshots cannot be cloned and (2)Shares cannot be rolled back to read-only snapshots" >' + c.name;
                }
                html += '</label>';
            });
            return new Handlebars.SafeString(html);
        });

    }
});

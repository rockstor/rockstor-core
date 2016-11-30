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

/*
 * Pools View
 */

PoolsView = RockstorLayoutView.extend({

    events: {
        "click a[data-action=delete]": "deletePool",
        'click #js-cancel': 'cancel',
        'click #js-confirm-pool-delete': 'confirmPoolDelete'
    },

    initialize: function() {

        this.constructor.__super__.initialize.apply(this, arguments);
        this.pools_table_template = window.JST.pool_pools_table;
        this.collection = new PoolCollection();
        this.disks = new DiskCollection();
        this.disks.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.disks);
        this.dependencies.push(this.collection);
        this.collection.on("reset", this.renderPools, this);
        this.initHandlebarHelpers();

    },

    render: function() {
        this.fetch(this.renderPools,this);
        return this;
    },

    renderPools: function() {
        var _this = this;
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }

        var freedisks = this.disks.filter(function(disk) {
            return (disk.get('pool') == null) && !(disk.get('offline')) &&
            !(disk.get('parted'));
        });

        var disksAvailable = false;
        if(_.size(freedisks) > 0){
            disksAvailable = true;
        }

        $(this.el).html(this.pools_table_template({
            collection: this.collection,
            poolCollection: this.collection.toJSON(),
            collectionNotEmpty: !this.collection.isEmpty(),
            disksAvailable: disksAvailable
        }));

        this.$('[rel=tooltip]').tooltip({placement: 'bottom'});

        this.renderDataTables();

        //X-editable Inline Edit.
        $.fn.editable.defaults.mode = 'inline';
        $('.status').editable({
            source: [
                     {value: 'no', text: 'no'},
                     {value: 'zlib', text: 'zlib'},
                     {value: 'lzo', text: 'lzo'}
                     ],
                     success: function(response, newCompr){
                         //use $(this) to dynamically get pool name from select dropdown.
                         var poolName = $(this).data('pname');
                         var mntOptn = $(this).data('mntoptn');
                         $.ajax({
                             url: "/api/pools/" + poolName + '/remount',
                             type: "PUT",
                             dataType: "json",
                             data: {
                                 "compression": newCompr,
                                 "mnt_options": mntOptn
                             },
                         });
                     }
        });

        $('.mntOptns').editable({
            title: 'Edit Mount Options',
            emptytext: 'None',
            success: function(response, newMntOptns){
                var poolName = $(this).data('pname');
                var compr = $(this).data('comp');
                $.ajax({
                    url: "/api/pools/" + poolName + '/remount',
                    type: "PUT",
                    dataType: "json",
                    data: {
                        "compression": compr,
                        "mnt_options": newMntOptns
                    },
                });
            }
        });

        return this;
    },

    displayPoolInformation: function (poolName) {
        // set share name in confirm dialog
        // this.$('#pass-pool-name').html(poolName);
        //show the dialog
        this.$('#delete-pool-modal-' + poolName).modal();
        return false;
    },

    deletePool: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        var $poolShares = $("#pool-shares");
        // Remove share names upon reopening
        $poolShares.html("");
        if (buttonDisabled(button)) return false;
        var poolName = button.attr('data-name');
        var poolShares = new PoolShareCollection([], {poolName: poolName});
        poolShares.fetch({
            success: function (data) {
                var shares = poolShares.models[0].attributes.results;
                // Only display shares if they exist
                if (!_.isUndefined(shares)) {
                    _.each(shares, function(share) {
                        $poolShares.append("<li>" + share.name +  " (" + share.size_gb + " GB)</li>");
                    });
                    _this.displayPoolInformation(poolName);
                }
            },
            error: function (err) {
                // Display anyways
                _this.displayPoolInformation(poolName);
            }
        });
    },

    confirmPoolDelete: function(event) {
        var _this = this;
        var button = $(event.currentTarget);
        if (buttonDisabled(button)) return false;
        disableButton(button);
        var poolName = button.attr('data-name');
        var url = "/api/pools/" + poolName + "/force";
        $.ajax({
            url: url,
            type: "DELETE",
            dataType: "json",
            success: function() {
                enableButton(button);
                _this.$('#delete-pool-modal-' + poolName).modal('hide');
                $('.modal-backdrop').remove();
                _this.render();
            },
            error: function(xhr, status, error) {
                enableButton(button);
            }
        });
    },

    cancel: function(event) {
        if (event) event.preventDefault();
        app_router.navigate('pools', {trigger: true})
    },

    initHandlebarHelpers: function(){
        Handlebars.registerHelper('humanReadableSize', function(type, size, poolReclaim, poolFree) {
            var html = '';
            if(type == "size"){
                html += humanize.filesize(size * 1024);
            }else if(type == "usage"){
                html += humanize.filesize((size - poolReclaim - poolFree) * 1024);
            }else if (type == "usagePercent"){
                html += (((size - poolReclaim - poolFree) / size) * 100).toFixed(2);
            }
            return new Handlebars.SafeString(html);

        });

        Handlebars.registerHelper('checkCompressionStatus', function(poolCompression, opts) {
            if (poolCompression == 'no' || _.isNull(poolCompression) || _.isUndefined(poolCompression) ) {
                return opts.fn(this);
            }
            return opts.inverse(this);
        });

        Handlebars.registerHelper('getDisks', function(disks) {
            var dNames =  _.reduce(disks,
                    function(s, disk, i, list) {
                if (i < (list.length-1)){
                    return s + disk.name + ',';
                } else {
                    return s + disk.name;
                }
            }, '');
            return dNames;
        });

        Handlebars.registerHelper('isRoot', function(role) {
            if (role == 'root') {
                return true;
            }
            return false;
        });
    }
});

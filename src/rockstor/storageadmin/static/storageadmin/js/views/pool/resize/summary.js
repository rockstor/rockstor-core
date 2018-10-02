/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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


PoolResizeSummary = RockstorWizardPage.extend({

    initialize: function() {
        this.template = window.JST.pool_resize_summary;
        var choice = this.model.get('choice');
        var raidLevel = null;
        var diskIdtoNameMap = new Map();
        // Extract the selected disks ids and names.
        var selectedDiskIds = [];
        if (!_.isUndefined(this.model.get('diskIds'))) {
            this.model.get('diskIds').forEach(function (diskInfo) {
                var diskInfoAsObj = JSON.parse(diskInfo);
                diskIdtoNameMap.set(diskInfoAsObj.id, diskInfoAsObj.name);
                selectedDiskIds.push(diskInfoAsObj.id);
            });
        }
        this.model.set('selectedDiskIds', selectedDiskIds);
        var poolDiskIds = _.map(this.model.get('pool').get('disks'), function(disk) {
            diskIdtoNameMap.set(disk.id, disk.name);
            return disk.id;
        });
        this.model.set('diskIdtoNameMap', diskIdtoNameMap)
        if (choice == 'add') {
            this.newRaidLevel = this.model.get('raidChange') ? this.model.get('raidLevel') :
                this.model.get('pool').get('raid');
            this.proposedDiskIds = _.union(poolDiskIds, selectedDiskIds);
        } else if (choice == 'remove') {
            this.newRaidLevel = this.model.get('pool').get('raid');
            this.proposedDiskIds = _.difference(poolDiskIds, selectedDiskIds);
        } else if (choice == 'raid') {
            this.newRaidLevel = this.model.get('raidLevel');
            this.proposedDiskIds = _.union(poolDiskIds, selectedDiskIds);
        }
        // Retrieve proposed disk names from proposedDiskIds
        var proposedDisksByName = [];
        this.proposedDiskIds.forEach(function(diskId) {
            proposedDisksByName.push(diskIdtoNameMap.get(diskId))
        });

        this.newDisks = proposedDisksByName;

        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    render: function() {
        $(this.el).html(this.template({
            model: this.model,
            poolName: this.model.get('pool').get('name'),
            raidLevel: this.model.get('pool').get('raid'),
            newRaidLevel: this.newRaidLevel,
            newDisks: this.newDisks
        }));
        return this;
    },

    save: function() {
        var _this = this;
        document.getElementById('next-page').disabled = true;
        var choice = this.model.get('choice');
        var raidLevel = null;
        if (choice == 'add') {
            raidLevel = this.model.get('raidChange') ? this.model.get('raidLevel') :
                this.model.get('pool').get('raid');
            return $.ajax({
                url: '/api/pools/' + this.model.get('pool').get('id') + '/add',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'disks': this.model.get('selectedDiskIds'),
                    'raid_level': raidLevel
                }),
                success: function() {
                    document.getElementById('next-page').disabled = false;
                },
                error: function(request, status, error) {}
            });
        } else if (choice == 'remove') {
            return $.ajax({
                url: '/api/pools/' + this.model.get('pool').get('id') + '/remove',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'disks': this.model.get('selectedDiskIds'),
                    'raid_level': this.model.get('pool').get('raid')
                }),
                success: function() {
                    document.getElementById('next-page').disabled = false;
                },
                error: function(request, status, error) {}
            });
        } else if (choice == 'raid') {
            return $.ajax({
                url: '/api/pools/' + this.model.get('pool').get('id') + '/add',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'disks': this.model.get('selectedDiskIds'),
                    'raid_level': this.model.get('raidLevel')
                }),
                success: function() {
                    document.getElementById('next-page').disabled = false;
                },
                error: function(request, status, error) {}
            });
        }
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_diskSet', function() {
            var html = '';
            html += _.map(this.model.get('pool').get('disks'), function(disk) {
                return disk.name;
            }).join(',');
            return new Handlebars.SafeString(html);
        });

        // potentially a display_diskSet_proposed handlebars helper

        Handlebars.registerHelper('display_breadCrumbs', function() {
            var html = '';
            if (this.model.get('choice') == 'add') {
                html += '<div>Change RAID level?</div><div>Select disks to add</div>';
            } else if (this.model.get('choice') == 'remove') {
                html += '<div>Select disks to remove</div>';
            } else if (this.model.get('choice') == 'raid') {
                html += '<div>Select RAID level and add disks</div>';
            }
            return new Handlebars.SafeString(html);
        });

    }
});

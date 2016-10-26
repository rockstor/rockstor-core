/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2016 RockStor, Inc. <http://rockstor.com>
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

var SnapperMainView = RockstorLayoutView.extend({
    events: {
        'click button#config-delete': 'onConfigDeleteClicked',
        'click button#select': function() {
            this.table.rows().select();
        },
        'click button#unselect': function() {
            this.table.rows().deselect();
        },
        'click button#delete': 'onDeleteClicked'
    },

    initialize: function() {
        this.template = window.JST.snapper_main;
        this.collection = new SnapperConfigCollection();
        this.selector = new BootstrapSelect({
            collection: this.collection
        });
        this.selectedSnapshots = [];
        this.listenTo(this.collection, 'change:snapshots', this.updateSnapshots);
        this.listenTo(this.selector, 'change:selection', this.updateSelectedConfig);
        this.collection.fetch();
    },

    render: function() {
        this.$el.html(this.template);
        this.selector.setElement(this.$('select#config'));
        this.table = this.$('table').DataTable({
            order: [[2,'asc']],
            select: true,
            columns: [
                {data: 'number', title: 'ID'},
                {data: 'type', title: 'Type'},
                {data: 'timestamp', title: 'Start Time'},
                {data: 'end_time', title: 'End Time'},
                {data: 'description', title: 'Description'},
                {data: 'cleanup', title: 'Cleanup Algorithm'},
                {data: 'userdata', title: 'User Data'}
            ]
        });

        // Enable snapshot delete button only when there is a selection
        var deleteButton = this.$('#delete');
        disableButton(deleteButton);
        this.table.on('select.dt deselect.dt', function(event, dt, type, indexes) {
            if (dt.rows({selected: true}).count())
                enableButton(deleteButton);
            else
                disableButton(deleteButton);
        });
        return this;
    },

    updateSelectedConfig: function(config) {
        this.$('h1 > span').text('for ' + config.get('SUBVOLUME'));
        config.snapshots.fetch();
    },

    updateSnapshots: function(config) {
        var data = [];
        config.snapshots.each(function(snapshot) {
            // Do some processing to combine pre/post snapshots into a single row
            var current = _.clone(snapshot.attributes);
            current.end_time = '';
            current.userdata = _.map(current.userdata, function(value, key) {
                return key + '=' + value;
            }).join(', ');
            if (current.pre_number) {
                var pre = data[data.length-1];
                pre.number = pre.number + ', ' + current.number;
                pre.type += ', post';
                pre.end_time = current.timestamp;
            } else {
                data.push(current);
            }
        });
        this.table.clear().rows.add(data).draw();
    },

    onDeleteClicked: function() {
        // Filter out the list of IDs from the table selection.
        this.selectedSnapshots = this.table
            .rows({selected: true})
            .data()
            .pluck('number')
            .join(' ')
            .match(/\d+/g);

        // Show confirmation dialog if multiple snapshots are to be deleted at
        // once.
        if (!this.selectedSnapshots) {
            return;
        } else if (this.selectedSnapshots.length == 1) {
            this.deleteSnapshots();
        } else {
            var dialog = new WarningDialog({
                el: this.$('.snapper-modal'),
                message: 'You are about to delete multiple snapshots. ' +
                    'This action cannot be undone. Proceed?'
            }).render();
            dialog.once('submit', this.deleteSnapshots, this);
        }
    },

    deleteSnapshots: function() {
        this.selector.model.snapshots.remove(this.selectedSnapshots);
    },

    onConfigDeleteClicked: function() {
        var dialog = new WarningDialog({
            el: this.$('.snapper-modal'),
            message: 'All snapshots associated with the selected configuration ' +
                'will also be deleted. This action cannot be undone. Proceed?'
        }).render();
        dialog.once('submit', function() {
            this.selector.model.destroy();
        }, this);
    }
});


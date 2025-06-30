/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>
 *
 * Rockstor is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 *
 * Rockstor is distributed in the hope that it will be useful, but
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

SnapshotsCommonView = RockstorLayoutView.extend({
    selectSnapshot: function(event) {
        var _this = this;
        var name = $(event.currentTarget).attr('data-name');
        var checked = $(event.currentTarget).prop('checked');
        this.selectSnapshotWithName(name, checked);
        this.toggleDeleteButton();
    },

    selectSnapshotWithName: function(name, checked) {
        if (checked) {
            if (!RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
                RockstorUtil.addToList(
                    this.selectedSnapshots, this.collection, 'name', name);
            }
        } else {
            if (RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
                RockstorUtil.removeFromList(this.selectedSnapshots, 'name', name);
            }
        }
    },

    toggleDeleteButton: function() {
        if (this.selectedSnapshots.length == 0) {
            $('#js-snapshot-delete-multiple').css('visibility', 'hidden');
        } else {
            $('#js-snapshot-delete-multiple').css('visibility', 'visible');
        }
    },

    selectAllSnapshots: function(event) {
        var _this = this;
        var checked = $(event.currentTarget).prop('checked');
        this.$('.js-snapshot-select').prop('checked', checked);
        this.$('.js-snapshot-select').each(function() {
            _this.selectSnapshotWithName($(this).attr('data-name'), checked);
        });
        this.toggleDeleteButton();
    },
});
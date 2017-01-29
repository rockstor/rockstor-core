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

PoolResizeWizardView = WizardView.extend({
    initialize: function() {
        WizardView.prototype.initialize.apply(this, arguments);
        this.pages = [];
    },

    setCurrentPage: function() {
        var choice = this.model.get('choice');
        var page = null;
        if (_.isUndefined(this.pages[this.currentPageNum]) ||
            _.isNull(this.pages[this.currentPageNum])) {
            if (_.isUndefined(choice)) {
                this.pages[0] = PoolResizeChoice;
            } else if (choice == 'add') {
                this.pages[1] = PoolAddDisksRaid;
                this.pages[2] = PoolAddDisks;
                this.pages[3] = PoolResizeSummary;
                this.pages[4] = PoolRemoveDisksComplete;
            } else if (choice == 'remove') {
                this.pages[1] = PoolRemoveDisks;
                this.pages[2] = PoolResizeSummary;
                this.pages[3] = PoolRemoveDisksComplete;
            } else if (choice == 'raid') {
                this.pages[1] = PoolRaidChange;
                this.pages[2] = PoolResizeSummary;
                this.pages[3] = PoolRemoveDisksComplete;
            }
        }
        this.currentPage = new this.pages[this.currentPageNum]({
            model: this.model,
            parent: this,
            evAgg: this.evAgg
        });
    },

    lastPage: function() {
        return ((this.pages.length > 1) &&
            ((this.pages.length - 1) == this.currentPageNum));
    },

    modifyButtonText: function() {
        switch (this.currentPageNum) {
        case 0:
            this.$('#ph-wizard-buttons').hide();
            this.model.unset('choice');
            this.pages = [];
            this.setCurrentPage();
            break;
        default:
            this.$('#ph-wizard-buttons').show();
            break;
        }
        if (this.pages[this.currentPageNum] == PoolResizeSummary) {
            this.$('#next-page').html('Resize');
        } else if (this.lastPage()) {
            this.$('#prev-page').hide();
            this.$('#next-page').html('Finish');
        } else {
            this.$('#next-page').html('Next');
        }
    },

    finish: function() {
        this.parent.$('#pool-resize-raid-overlay').overlay().close();
        this.parent.render();
    },

});
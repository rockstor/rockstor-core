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

PoolResizeChoice = RockstorWizardPage.extend({

    initialize: function() {
        this.template = window.JST.pool_resize_choice;
        RockstorWizardPage.prototype.initialize.apply(this, arguments);
        this.initHandlebarHelpers();
    },

    events: {
        'click #change-raid': 'changeRaid',
        'click #add-disks': 'addDisks',
        'click #remove-disks': 'removeDisks'
    },

    changeRaid: function() {
        this.model.set('choice', 'raid');
        this.evAgg.trigger('nextPage');
        return false;
    },

    addDisks: function() {
        this.model.set('choice', 'add');
        this.evAgg.trigger('nextPage');
        return false;
    },

    removeDisks: function() {
        this.model.set('choice', 'remove');
        this.parent.nextPage();
        return false;
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_poolName', function() {
            var poolName = '';
            poolName = this.model.get('pool').get('name');
            return new Handlebars.SafeString(poolName);
        });

    }

});

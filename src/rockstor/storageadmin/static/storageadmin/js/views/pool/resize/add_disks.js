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


PoolAddDisks = RockstorWizardPage.extend({

    initialize: function() {
	this.disks = new DiskCollection();
	this.disks.setPageSize(100);
	this.template = window.JST.pool_resize_add_disks;
	this.disks_template = window.JST.common_disks_table;
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.disks.on('reset', this.renderDisks, this);
    },

    render: function() {
	RockstorWizardPage.prototype.render.apply(this, arguments);
	this.disks.fetch();
	return this;
    },

    renderDisks: function() {
	var disks = this.disks.filter(function(disk) {
	    return disk.available();
	}, this);
	this.$('#ph-disks-table').html(this.disks_template({disks: disks}));
    },

    save: function() {
	var _this = this;
	var checked = this.$(".diskname:checked").length;
	var diskNames = [];
	this.$(".diskname:checked").each(function(i) {
	    diskNames.push($(this).val());
	});
	this.model.set('diskNames', diskNames);
	if (this.model.get('raidChange')) {
	    this.model.set('raidLevel', this.$('#raid-level').val());
	}
	return $.Deferred().resolve();
    }
});

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

PoolRaidChange = RockstorWizardPage.extend({

    initialize: function() {
	this.disks = new DiskCollection();
	this.disks.setPageSize(100);
	this.template = window.JST.pool_resize_raid_change;
	this.disks_template = window.JST.common_disks_table;
	RockstorWizardPage.prototype.initialize.apply(this, arguments);
	this.disks.on('reset', this.renderDisks, this);
    },

    render: function() {
	$(this.el).html(this.template({model: this.model}));
	this.disks.fetch();
	return this;
    },

    renderDisks: function() {
	var _this = this;
	var disks = this.disks.filter(function(disk) {
	    return disk.available();
	}, this);
	this.$('#raid-change-form').validate({
	    rules: {
		'raid-level': {
		    required: true
		}
	    },
	    messages: {
		'raid-level': 'Please select a RAID level'
	    }
	});
    },

    save: function() {
	var valid = $('#raid-change-form').valid();
	if (valid) {
	    var raidLevel = this.$('#raid-level').val();
	    this.model.set('raidLevel', raidLevel);
	    return $.Deferred().resolve();
	}
	return $.Deferred().reject();
    }

});

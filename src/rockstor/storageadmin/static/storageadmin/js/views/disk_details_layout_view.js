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

DiskDetailsLayoutView = RockstorLayoutView.extend({

    initialize: function() {
	// call initialize of base
	this.constructor.__super__.initialize.apply(this, arguments);
	this.diskName = this.options.diskName;
	this.template = window.JST.disk_disk_details_layout;
	this.disk = new Disk({diskName: this.diskName});
	this.smartinfo = new SmartInfo({diskName: this.diskName});
	this.dependencies.push(this.disk);
	this.dependencies.push(this.smartinfo);
    },

    render: function() {
	this.fetch(this.renderSubViews, this);
	return this;
    },

    renderSubViews: function() {
	console.log('smartinfo', this.smartinfo);
	$(this.el).html(this.template({disk: this.disk, smartinfo: this.smartinfo}));
	this.$("ul.css-tabs").tabs("div.css-panes > div");
    }
});

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

RockonsView = RockstorLayoutView.extend({


    initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.rockons_rockons;
	this.rockons = new RockOnCollection({});
	this.dependencies.push(this.rockons);

    },

    render: function() {
	this.fetch(this.renderRockons, this);
	return this;
    },

    renderRockons: function() {
	var _this = this;
	// render template
	//$(this.el).empty();
	//$(this.el).append(this.template());
	$(this.el).html(this.template({rockons: this.rockons}));
	this.dockerServiceView = new DockerServiceView({
	    parentView: this,
	    dockerService: this.dockerService
	});

	$('#docker-service-ph').append(this.dockerServiceView.render().el);
	console.log('rockons');
	console.log(this.rockons);
	this.$("ul.css-tabs").tabs("div.css-panes > div");
    },


});

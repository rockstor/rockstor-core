
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

ReplicaTrailsView = RockstorLayoutView.extend({
	events: {
	},

	initialize: function() {
		// call initialize of base
		this.constructor.__super__.initialize.apply(this, arguments);
		// set template
		this.template = window.JST.replication_replica_trails;
		// add dependencies
		this.replicaId = this.options.replicaId;
		this.replica = new Replica({id: this.replicaId});
		this.dependencies.push(this.replica);
		this.collection = new ReplicaTrailCollection(null, {
			replicaId: this.replicaId
		});
		this.collection.pageSize = 10;
		this.dependencies.push(this.collection);
		this.collection.on("reset", this.renderReplicaTrails, this);
		// has the replica been fetched? prevents renderReplicaTrails executing
		// (because of collection reset) before replica has been fetched
		this.replicaFetched = false;
		this.initHandlebarHelpers();
	},

	render: function() {
		this.fetch(this.firstFetch, this);
		return this;
	},

	firstFetch: function() {
		this.replicaFetched = true;
		this.renderReplicaTrails();
	},

	renderReplicaTrails: function() {
		if (!this.replicaFetched) return false;
		var _this = this;
		$(this.el).html(this.template({
			replica: _this.replica.toJSON(),
			replicaColl: _this.collection.toJSON(),
			collection: _this.collection,
			collectionNotEmpty: !this.collection.isEmpty()
		}));
		// remove existing tooltips
		if (this.$('[rel=tooltip]')) {
			this.$('[rel=tooltip]').tooltip('hide');
		}
		this.$('[rel=tooltip]').tooltip({ placement: 'bottom'});
	},

	initHandlebarHelpers: function(){
		Handlebars.registerHelper('replicaTrails_table', function(){
			var html = '',
			_this = this;
			this.collection.each(function(r) {
				html += '<tr>';
				html += '<td>' + r.get('id') + '</td>';
				html += '<td>' + r.get('snap_name') + '</td>';
				html += '<td>' + moment(r.get('snapshot_created')).format(RS_DATE_FORMAT) + '</td>';
				html += '<td>';
				if (r.get('end_ts')) {
					html += moment(r.get('end_ts')).format(RS_DATE_FORMAT);
				}
				html += '</td>';
				html += '<td>';
				if (r.get('status') != 'failed') {
					html += r.get('status');
				} else {
					html += '<i class="fa fa-exclamation-circle" title="' + r.get('error') + '" rel="tooltip"></i>&nbsp;' + r.get('status');
				}
				html += '</td>';
				html += '<td>';
				if (r.get('end_ts')) {
					html += moment(r.get('end_ts')).from(moment(r.get('snapshot_created')));
				} else {
				}
				html += '</td>';
				html += '<td>';
				if (r.get('end_ts')) {
					var d = moment(r.get('end_ts')).diff(moment(r.get('snapshot_created')))/1000;
					var rate = (r.get('kb_sent') / d).toFixed(2);
				} else {
					var d = moment().diff(moment(r.get('snapshot_created')))/1000;
					var rate = (r.get('kb_sent') / d).toFixed(2);
				}
				html += r.get('kb_sent') + ' KB at ' + rate + ' KB/sec.';
				html += '</td>';
				html += '</tr>';
			});
			return new Handlebars.SafeString(html);
		});
	}


});

//Add pagination
Cocktail.mixin(ReplicaTrailsView, PaginationMixin);

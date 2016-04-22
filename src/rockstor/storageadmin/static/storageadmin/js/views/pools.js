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

/*
 * Pools View
 */

PoolsView = RockstorLayoutView.extend({
	events: {
		"click a[data-action=delete]": "deletePool",
		'click #js-cancel': 'cancel',
		'click #js-confirm-pool-delete': 'confirmPoolDelete'
	},

	initialize: function() {

		this.constructor.__super__.initialize.apply(this, arguments);
		this.pools_table_template = window.JST.pool_pools_table;
		this.collection = new PoolCollection();
		this.disks = new DiskCollection();
		this.disks.pageSize = RockStorGlobals.maxPageSize;
		this.dependencies.push(this.disks);
		this.dependencies.push(this.collection);
		this.collection.on("reset", this.renderPools, this);
		this.initHandlebarHelpers();

	},

	render: function() {
		this.fetch(this.renderPools,this);
		return this;
	},

	renderPools: function() {
		var _this = this;
		if (this.$('[rel=tooltip]')) {
			this.$('[rel=tooltip]').tooltip('hide');
		}

		var freedisks = this.disks.filter(function(disk) {
			return (disk.get('pool') == null) && !(disk.get('offline')) &&
			!(disk.get('parted'));
		});

		$(this.el).html(this.pools_table_template({
			collection: this.collection,
			poolCollection: this.collection.toJSON(),
			collectionNotEmpty: !this.collection.isEmpty(),
			noOfFreeDisks: _.size(freedisks)
		}));

		this.$("#pools-table").tablesorter({
			headers: {
				// assign the fifth column (we start counting zero)
				5: {
					// disable it by setting the property sorter to false
					sorter: false
				}
			}
		});
		this.$('[rel=tooltip]').tooltip({placement: 'bottom'});

		return this;
	},

	deletePool: function(event) {
		var _this = this;
		var button = $(event.currentTarget);
		if (buttonDisabled(button)) return false;
		poolName = button.attr('data-name');
		// set share name in confirm dialog
		_this.$('#pass-pool-name').html(poolName);
		//show the dialog
		_this.$('#delete-pool-modal').modal();
		return false;
	},

	//modal confirm button handler
	confirmPoolDelete: function(event) {
		var _this = this;
		var button = $(event.currentTarget);
		if (buttonDisabled(button)) return false;
		disableButton(button);
		$.ajax({
			url: "/api/pools/" + poolName,
			type: "DELETE",
			dataType: "json",
			success: function() {
				_this.collection.fetch({reset: true});
				enableButton(button);
				_this.$('#delete-pool-modal').modal('hide');
				$('.modal-backdrop').remove();
				app_router.navigate('pools', {trigger: true})
			},
			error: function(xhr, status, error) {
				enableButton(button);
			}
		});
	},

	cancel: function(event) {
		if (event) event.preventDefault();
		app_router.navigate('pools', {trigger: true})
	},

	initHandlebarHelpers: function(){
		Handlebars.registerHelper('getDisks', function(disks) {
			var dNames =  _.reduce(disks,
					function(s, disk, i, list) {
				if (i < (list.length-1)){
					return s + disk.name + ',';
				} else {
					return s + disk.name;
				}
			}, '');
			return dNames;
		});
		Handlebars.registerHelper('humanReadableSize', function(type, size, poolReclaim, poolFree) {
			var html = '';
			if(type == "size"){
				html += humanize.filesize(size * 1024);
			}else if(type == "usage"){
				html += humanize.filesize((size - poolReclaim - poolFree) * 1024);
			}else if (type == "usagePercent"){
				html += (((size - poolReclaim - poolFree) / size) * 100).toFixed(2);
			}
			return new Handlebars.SafeString(html);

		});

		Handlebars.registerHelper('getCompressionStatus', function(poolCompression) {
			if (poolCompression == 'no' || _.isNull(poolCompression) || _.isUndefined(poolCompression) ) {
				return true;
			}
			return false;
		});
		
		Handlebars.registerHelper('isRoot', function(role) {
			if (role == 'root') {
				return true;
			}
			return false;
		});

		//createPool button needs to appear after the table so, call another helper function
		Handlebars.registerHelper('print_CreatePool_Button', function() {
			var html = '',
			editIconGlyph = '<i class="glyphicon glyphicon-edit"></i>';
			if(this.noOfFreeDisks > 0){
				html += '<a href="#add_pool" id="add_pool" class="btn btn-primary">' + editIconGlyph + ' Create Pool</a>';
			}else{
				html += '<a  id="add_pool" class="btn btn-primary disabled" title="There are no Disks available to create a Pool at this time." >' + editIconGlyph + ' Create Pool</a>';
			}
			return new Handlebars.SafeString(html);
		});
	}
});


//Add pagination
Cocktail.mixin(PoolsView, PaginationMixin);

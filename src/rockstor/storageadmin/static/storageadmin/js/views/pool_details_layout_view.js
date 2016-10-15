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

PoolDetailsLayoutView = RockstorLayoutView.extend({

	initialize: function(options) {
		// call initialize of base
		this.constructor.__super__.initialize.apply(this, arguments);
		this.poolName = options.poolName;
		this.cView = options.cView;
		this.template = window.JST.pool_pool_details_layout;
		this.resize_pool_info_template = window.JST.pool_resize_pool_info;
		this.compression_info_template = window.JST.pool_compression_info;
		this.compression_info_edit_template = window.JST.pool_compression_info_edit;
		this.pool = new Pool({poolName: this.poolName});
		// create poolscrub models
		this.poolscrubs = new PoolscrubCollection([],{snapType: 'admin'});
		this.poolscrubs.pageSize = 5;
		this.poolscrubs.setUrl(this.poolName);
		// create pool re-balance models
		this.poolrebalances = new PoolRebalanceCollection([],{snapType: 'admin'});
		this.poolrebalances.pageSize = 5;
		this.poolrebalances.setUrl(this.poolName);

		this.dependencies.push(this.pool);
		this.dependencies.push(this.poolscrubs);
		this.dependencies.push(this.poolrebalances);
		this.disks = new DiskCollection();
		this.disks.pageSize = RockStorGlobals.maxPageSize;
		this.dependencies.push(this.disks);
		this.cOpts = {'no': 'Dont enable compression', 'zlib': 'zlib', 'lzo': 'lzo'};
		this.initHandlebarHelpers();

	},

	events: {
		'click #delete-pool': 'deletePool',
		"click #js-resize-pool": "resizePool",
		"click #js-submit-resize": "resizePoolSubmit",
		"click #js-resize-cancel": "resizePoolCancel",
		"click #js-edit-compression": "editCompression",
		"click #js-edit-compression-cancel": "editCompressionCancel",
		"click #js-submit-compression": "updateCompression",
	},

	render: function() {
		this.fetch(this.renderSubViews, this);
		return this;
	},

	renderSubViews: function() {
		var poolNameIsRockstor = false;
		if (this.pool.get('role') == 'root') {
			poolNameIsRockstor = true;
		}
		$(this.el).html(this.template({
			pool: this.pool,
			poolName: this.pool.get('name'),
			isPoolNameRockstor: poolNameIsRockstor,
		}));

		this.subviews['pool-info'] = new PoolInfoModule({ model: this.pool.toJSON() });
		this.subviews['pool-usage'] = new PoolUsageModule({ model: this.pool });
		this.subviews['pool-scrubs'] = new PoolScrubTableModule({poolscrubs: this.poolscrubs, pool: this.pool, parentView: this });
		this.subviews['pool-rebalances'] = new PoolRebalanceTableModule({poolrebalances: this.poolrebalances, pool: this.pool, parentView: this });
		this.pool.on('change', this.subviews['pool-info'].render, this.subviews['pool-info']);
		this.pool.on('change', this.subviews['pool-usage'].render, this.subviews['pool-usage']);
		this.poolscrubs.on('change', this.subviews['pool-scrubs'].render, this.subviews['pool-scrubs']);
		this.$('#ph-pool-info').html(this.subviews['pool-info'].render().el);
		this.$('#ph-pool-usage').html(this.subviews['pool-usage'].render().el);
		this.$('#ph-pool-scrubs').html(this.subviews['pool-scrubs'].render().el);
		this.$('#ph-pool-rebalances').html(this.subviews['pool-rebalances'].render().el);

		if (!_.isUndefined(this.cView) && this.cView == 'edit') {
			this.$('#ph-compression-info').html(this.compression_info_edit_template({
				pool: this.pool.toJSON(),
				cOpts: this.cOpts,
			}));
			this.showCompressionTooltips(); } else {
				this.$('#ph-compression-info').html(this.compression_info_template({
					pool: this.pool.toJSON(),
				})); }

		this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({pool:
			this.pool.toJSON()})); this.$("ul.nav.nav-tabs").tabs("div.css-panes > div"); if
			(!_.isUndefined(this.cView) && this.cView == 'resize') { // scroll to resize section
				$('#content').scrollTop($('#ph-resize-pool-info').offset().top); }

			//$('#pool-resize-raid-modal').modal({show: false});
			$('#pool-resize-raid-overlay').overlay({load: false});

	},

	deletePool: function() {
		var button = this.$('#delete-pool');
		if (buttonDisabled(button)) return false;
		if(confirm("Delete pool: "+ this.pool.get('name') + "... Are you sure?")){
			disableButton(button);
			$.ajax({
				url: "/api/pools/" + this.pool.get('name'),
				type: "DELETE",
				dataType: "json",
				data: { "name": this.pool.get('name') },
				success: function() {
					app_router.navigate('pools', {trigger: true});
				},
				error: function(xhr, status, error) {
					enableButton(button);
				}
			});
		}
	},


	resizePool: function(event) {
		event.preventDefault();
		var wizardView = new PoolResizeWizardView({
			model: new Backbone.Model({ pool: this.pool }),
			title: 'Resize Pool / Change RAID level for ' + this.pool.get('name'),
			parent: this
		});
		$('.overlay-content', '#pool-resize-raid-overlay').html(wizardView.render().el);
		$('#pool-resize-raid-overlay').overlay().load();
	},

	resizePoolSubmit: function(event) {
		event.preventDefault();
		var button = this.$('#js-submit-resize');
		if (buttonDisabled(button)) return false;
		if(confirm(" Are you sure about Resizing this pool?")){
			disableButton(button);
			var _this = this;
			var raid_level = $('#raid_level').val();
			var disk_names = [];
			var err_msg = "Please select atleast one disk";
			var n = _this.$(".disknew:checked").length;
			var m = _this.$(".diskadded:unchecked").length;
			var resize_msg = ('Resize is initiated. A balance process is kicked off to redistribute data. It could take a while. You can check the status in the Balances tab. Its finish marks the success of resize.');
			if(n >= 0){
				$('#pool-resize-raid-modal').modal('show');
			} else if(m > 0) {
				_this.$(".diskadded:unchecked").each(function(i) {
					if (i < m) {
						disk_names.push($(this).val());
					}
				});
				$.ajax({
					url: '/api/pools/'+_this.pool.get('name')+'/remove',
					type: 'PUT',
					dataType: 'json',
					contentType: 'application/json',
					data: JSON.stringify({"disks": disk_names, "raid_level": raid_level}),
					success: function() {
						_this.hideResizeTooltips();
						alert(resize_msg);
						_this.pool.fetch({
							success: function(collection, response, options) {
								_this.cView = 'view';
								_this.render();
							}
						});

					},
					error: function(request, status, error) {
						enableButton(button);
					}
				});
			}
		}
	},

	resizePoolCancel: function(event) {
		event.preventDefault();
		this.hideResizeTooltips();
		this.$('#ph-resize-pool-info').html(this.resize_pool_info_template({pool: this.pool}));
	},

	resizePoolModalSubmit: function(event) {
		var _this = this;
		var raid_level = $('#raid_level').val();
		var disk_names = [];
		var err_msg = "Please select atleast one disk";
		var n = _this.$(".disknew:checked").length;
		var m = _this.$(".diskadded:unchecked").length;
		var resize_msg = ('Resize is initiated. A balance process is kicked off to redistribute data. It could take a while. You can check the status in the Balances tab. Its finish marks the success of resize.');
		_this.$(".disknew:checked").each(function(i) {
			if (i < n) {
				disk_names.push($(this).val());
			}
		});
		$.ajax({
			url: '/api/pools/'+_this.pool.get('name')+'/add',
			type: 'PUT',
			dataType: 'json',
			contentType: 'application/json',
			data: JSON.stringify({"disks": disk_names, "raid_level": raid_level}),
			success: function() {
				_this.hideResizeTooltips();
				alert(resize_msg);
				_this.pool.fetch({
					success: function(collection, response, options) {
						_this.cView = 'view';
						_this.render();
					}
				});
			},
			error: function(request, status, error) {
				enableButton(button);
			}
		});

	},

	editCompression: function(event) {
		event.preventDefault();
		this.$('#ph-compression-info').html(this.compression_info_edit_template({
			pool: this.pool.toJSON(),
			cOpts: this.cOpts,
		}));
		this.showCompressionTooltips();
	},

	editCompressionCancel: function(event) {
		event.preventDefault();
		this.hideCompressionTooltips();
		this.$('#ph-compression-info').html(this.compression_info_template({
			pool: this.pool.toJSON(), 
		}));
	},

	updateCompression: function(event) {
		var _this = this;
		event.preventDefault();
		var button = this.$('#js-submit-compression');
		if (buttonDisabled(button)) return false;
		disableButton(button);
		$.ajax({
			url: "/api/pools/" + this.pool.get('name') + '/remount',
			type: "PUT",
			dataType: "json",
			data: {
				"compression": this.$('#compression').val(),
				"mnt_options": this.$('#mnt_options').val(),
			},
			success: function() {
				_this.hideCompressionTooltips();
				_this.pool.fetch({
					success: function(collection, response, options) {
						_this.cView = 'view';
						_this.renderSubViews();
					}
				});
			},
			error: function(xhr, status, error) {
				enableButton(button);
			}
		});
	},

	showCompressionTooltips: function() {
		this.$('#ph-compression-info #compression').tooltip({
			html: true,
			placement: 'top',
			container: 'body',
			title: "Choose a compression algorithm for this Pool.<br><strong>zlib: </strong>slower but higher compression ratio.<br><strong>lzo: </strong>faster compression/decompression, but ratio smaller than zlib.<br>Enabling compression at the pool level applies to all Shares carved out of this Pool.<br>Don't enable compression here if you like to have finer control at the Share level.<br>You can change the algorithm, disable or enable it later, if necessary."
		});
		this.$('#ph-compression-info #mnt_options').tooltip({ placement: 'top' });
	},

	hideCompressionTooltips: function() {
		this.$('#ph-compression-info #compression').tooltip('hide');
		this.$('#ph-compression-info #mnt_options').tooltip('hide');
	},

	showResizeTooltips: function() {
		this.$('#ph-resize-pool-info #raid_level').tooltip({
			html: true,
			placement: 'top',
			title: "You can transition raid level of this pool to change it's redundancy profile.",
		});
	},

	hideResizeTooltips: function() {
		this.$('#ph-resize-pool-info #raid_level').tooltip('hide');
	},

	attachModalActions: function() {

	},

	cleanup: function() {
		if (!_.isUndefined(this.statusIntervalId)) {
			window.clearInterval(this.statusIntervalId);
		}
	},

	initHandlebarHelpers: function(){

		Handlebars.registerHelper('getPoolCreationDate', function(date){
			return moment(date).format(RS_DATE_FORMAT);
		});
		
		Handlebars.registerHelper('isPoolCompressionNone', function(compression,opts){
			if (compression == 'no') {
				return opts.fn(this);
			}
			return opts.inverse(this);
		});

		Handlebars.registerHelper('isMntOptionNone', function(mtOptions,opts){
			if (_.isUndefined(mtOptions) || _.isNull(mtOptions) || _.isEmpty(mtOptions)) {
				return opts.fn(this);
			}  
			return opts.inverse(this);
		});
		
		Handlebars.registerHelper('selectedCompressionOption', function(existingComp,c,opts){
			if (existingComp == c) {
				return opts.fn(this);
			}  
			return opts.inverse(this);
		});

		Handlebars.registerHelper('humanReadableSize', function(size){
			return humanize.filesize(size * 1024);
		});
	}
});

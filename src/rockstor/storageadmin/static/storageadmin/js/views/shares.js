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
 * Shares View
 */

SharesView = RockstorLayoutView.extend({
	events: {
		"click a[data-action=delete]": "deleteShare",
		'click #js-cancel': 'cancel',
		'click #js-confirm-share-delete': 'confirmShareDelete'
	},

	initialize: function() {
		this.constructor.__super__.initialize.apply(this, arguments);

		this.template = window.JST.share_shares;
		this.shares_table_template = window.JST.share_shares_table;
		this.pools = new PoolCollection();
		this.collection = new ShareCollection();
		this.dependencies.push(this.pools);
		this.dependencies.push(this.collection);
		this.pools.on("reset", this.renderShares, this);
		this.collection.on("reset", this.renderShares, this);
		this.initHandlebarHelpers();
	},

	render: function() {
		this.fetch(this.renderShares, this);
		return this;
	},

	renderShares: function() {
		if (this.$('[rel=tooltip]')) {
			this.$('[rel=tooltip]').tooltip('hide');
		}
		if (!this.pools.fetched || !this.collection.fetched) {
			return false;
		}
		$(this.el).html(this.template({
			collection: this.collection,
			pools: this.pools
		}));
		this.$("#shares-table-ph").html(this.shares_table_template({
			collection: this.collection,
			shares: this.collection.toJSON(),
			collectionNotEmpty: !this.collection.isEmpty(),
			pools: this.pools,
			poolsNotEmpty: !this.pools.isEmpty()
		}));

		this.$('[rel=tooltip]').tooltip({placement: 'bottom'});

		this.renderDataTables();
	},

//	delete button handler
	deleteShare: function(event) {
		var _this = this;
		var button = $(event.currentTarget);
		if (buttonDisabled(button)) return false;
		shareName = button.attr('data-name');
		shareUsage = button.attr('data-usage');
		// set share name in confirm dialog
		_this.$('.pass-share-name').html(shareName);
		_this.$('#pass-share-usage').html(shareUsage);
		//show the dialog
		_this.$('#delete-share-modal').modal();
		return false;
	},

	confirmShareDelete: function(event) {
		var _this = this;
		var button = $(event.currentTarget);
		if (buttonDisabled(button)) return false;
		disableButton(button);
		var url = "/api/shares/" + shareName;
		if($("#force-delete").prop("checked")){
			url += "/force";
		}
		$.ajax({
			url: url,
			type: "DELETE",
		    dataType: "json",
			success: function() {
				_this.collection.fetch({reset: true});
				enableButton(button);
				_this.$('#delete-share-modal').modal('hide');
				$('.modal-backdrop').remove();
				app_router.navigate('shares', {trigger: true})
			},
			error: function(xhr, status, error) {
				enableButton(button);
			}
		});
	},
	cancel: function(event) {
		if (event) event.preventDefault();
		app_router.navigate('shares', {trigger: true})
	},

	initHandlebarHelpers: function(){

		Handlebars.registerHelper('humanize_size', function(num) {
			return humanize.filesize(num * 1024);
		});
		Handlebars.registerHelper('displayCompressionAlgo', function(shareCompression,shareName) {
			var html = '';
			if(shareCompression && shareCompression != 'no'){
				html += shareCompression;
			}else{
				html += 'None(defaults to pool level compression, if any)   ' +
				'<a href="#shares/' + shareName + '/?cView=edit"><i class="glyphicon glyphicon-pencil"></i></a>';
			}
			return new Handlebars.SafeString(html);
		});
	}
});
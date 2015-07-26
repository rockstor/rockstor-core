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

SnapshotsView  = RockstorLayoutView.extend({
	events: {
	"click #js-snapshot-add": "add",
	"click #js-snapshot-cancel": "cancel",
	"click .js-snapshot-delete": "deleteSnapshot",
	"click .js-snapshot-clone": "cloneSnapshot",
	"click .js-snapshot-select": "selectSnapshot",
	"click .js-snapshot-select-all": "selectAllSnapshots",
	"click #js-snapshot-delete-multiple": "deleteMultipleSnapshots"
},

initialize: function() {
	this.constructor.__super__.initialize.apply(this, arguments);
	this.template = window.JST.share_snapshots;
	this.paginationTemplate = window.JST.common_pagination;
	this.addTemplate = window.JST.share_snapshot_add_template;
	this.module_name = 'snapshots';
	this.snapshots = this.options.snapshots;
	this.collection = new SnapshotsCollection();
	this.shares = new ShareCollection();
	this.dependencies.push(this.shares);
	this.dependencies.push(this.collection);
	this.selectedSnapshots = [];
	this.replicaShareMap = {};
	this.snapShares = [];

	this.modify_choices = [
	                       {name: 'yes', value: 'yes'},
	                       {name: 'no', value: 'no'},
	                       ];
	this.parentView = this.options.parentView;
	this.collection.on("reset", this.renderSnapshots, this);

},

render: function() {
	this.fetch(this.renderSnapshots, this);
	return this;
},


renderSnapshots: function() {
	var _this = this;
	$(this.el).empty();

	$(this.el).append(this.template({
		snapshots: this.collection,
		selectedSnapshots: this.selectedSnapshots,
		share: this.share,
		shares: this.shares,
	}));
	this.$('[rel=tooltip]').tooltip({
		placement: 'bottom'
	});
	this.$('#snapshots-table').tablesorter({
		headers: { 0: {sorter: false}}
	});
	this.$(".pagination-ph").html(this.paginationTemplate({
		collection: this.collection
	}));
	return this;
},

setShareName: function(shareName) {
	this.collection.setUrl(shareName);
},

add: function(event) {
	var _this = this;
	event.preventDefault();
	$(this.el).html(this.addTemplate({
		snapshots: this.collection,
		share: this.share,
		shares: this.shares,
		modify_choices: this.modify_choices

	}));
	this.$('#shares').chosen();
	var err_msg = '';
	var name_err_msg = function() {
		return err_msg;
	}

	$.validator.addMethod('validateSnapshotName', function(value) {
		var snapshot_name = $('#snapshot-name').val();
		if (snapshot_name == "") {
			err_msg = 'Please enter snapshot name';
			return false;
		}
		else
			if(/^[A-Za-z][A-Za-z0-9_.-]*$/.test(snapshot_name) == false){
				err_msg = 'Please enter a valid snapshot name.';
				return false;
			}
		return true;
	}, name_err_msg);

	this.$('#add-snapshot-form :input').tooltip({placement: 'right'});
	this.validator = this.$('#add-snapshot-form').validate({
		onfocusout: false,
		onkeyup: false,
		rules: {
		'snapshot-name': 'validateSnapshotName',
		shares: 'required',
	},
	submitHandler: function() {
		var button = _this.$('#js-snapshot-save');
		var shareName = $("#shares").val();
		if (buttonDisabled(button)) return false;
		disableButton(button);
		$.ajax({
			url: "/api/shares/" + shareName+ "/snapshots/" + _this.$('#snapshot-name').val(),
			type: "POST",
			dataType: "json",
			contentType: 'application/json',
			data: JSON.stringify(_this.$('#add-snapshot-form').getJSON()),
			success: function() {
			_this.$('#add-snapshot-form :input').tooltip('hide');
			enableButton(button);
			_this.collection.fetch({
				success: function(collection, response, options) {
			}
			});
		},
		error: function(xhr, status, error) {
			_this.$('#add-snapshot-form :input').tooltip('hide');
			enableButton(button);
		}
		});

		return false;
	}
	});
},

deleteSnapshot: function(event) {
	event.preventDefault();
	var _this = this;
	var name = $(event.currentTarget).attr('data-name');
	var shareName = $(event.currentTarget).attr('data-share-name');
	var esize = $(event.currentTarget).attr('data-size');
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	if(confirm("Deleting snapshot("+ name +") deletes "+ esize +" of data permanently. Do you really want to delete it?")){
		disableButton(button);
		$.ajax({
			url: "/api/shares/" + shareName + "/snapshots/" + name,
			type: "DELETE",
			success: function() {
			enableButton(button)
			_this.$('[rel=tooltip]').tooltip('hide');
			_this.selectedSnapshots = [];
			_this.collection.fetch({reset: true});

		},
		error: function(xhr, status, error) {
		    enableButton(button);
		    _this.$('[rel=tooltip]').tooltip('hide');
		}
		});
	}
},

cloneSnapshot: function(event) {
	if (event) event.preventDefault();
	// Remove current tooltips to prevent them hanging around
	// even after new page has loaded.
	this.$('[rel=tooltip]').tooltip('hide');
	var name = $(event.currentTarget).attr('data-name');
	var url = 'shares/' + this.share.get('name') + '/snapshots/' +
			name + '/create-clone';
	app_router.navigate(url, {trigger: true});

},

selectSnapshot: function(event) {
	var _this = this;
	id = $(event.currentTarget).attr('data-id');
	var checked = $(event.currentTarget).prop('checked');
	this.selectSnapshotWithId(id, checked);
},

selectSnapshotWithId: function(id, checked) {
	if (checked) {
		if (!RockstorUtil.listContains(this.selectedSnapshots, 'id', id)) {
			RockstorUtil.addToList(
					this.selectedSnapshots, this.collection, 'id', id);
		}
	} else {
		if (RockstorUtil.listContains(this.selectedSnapshots, 'id', id)) {
			RockstorUtil.removeFromList(this.selectedSnapshots, 'id', id);
		}
	}
},


selectAllSnapshots: function(event) {
	var _this = this;
	var checked = $(event.currentTarget).prop('checked');
	this.$('.js-snapshot-select').prop('checked', checked)
	this.$('.js-snapshot-select').each(function() {
		_this.selectSnapshotWithId($(this).attr('data-id'), checked);
	});
},

deleteMultipleSnapshots: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	if (this.selectedSnapshots.length == 0) {
		alert('Select at least one snapshot to delete');
	} else {
		var confirmMsg = null;
		if (this.selectedSnapshots.length == 1) {
			confirmMsg = 'Deleting snapshot ';
		} else {
			confirmMsg = 'Deleting snapshots ';
		}
		var snapNames = _.reduce(this.selectedSnapshots, function(str, snap) {
			return str + snap.get('name') + ',';
		}, '', this);
		snapNames = snapNames.slice(0, snapNames.length-1);

		var snapIds = _.reduce(this.selectedSnapshots, function(str, snap) {
			return str + snap.id + ',';
		}, '', this);
		snapIds = snapIds.slice(0, snapIds.length-1);

		var totalSize = _.reduce(this.selectedSnapshots, function(sum, snap) {
			return sum + snap.get('eusage');
		}, 0, this);

		var totalSizeStr = humanize.filesize(totalSize*1024);

		if (confirm(confirmMsg + snapNames + ' deletes ' + totalSizeStr + ' of data. Are you sure?')) {
			disableButton(button);

			_.each(this.selectedSnapshots, function(s) {
				var name = s.get('name');

				_this.shares.each(function(share, index) {
					if(s.get('share')== share.get('id')){
						var shareName = share.get('name');
						$.ajax({
							url: "/api/shares/" + shareName + "/snapshots/" + name,
							type: "DELETE",
							success: function() {
							enableButton(button)
							_this.$('[rel=tooltip]').tooltip('hide');
							_this.selectedSnapshots = [];
							_this.collection.fetch({reset: true});

						},
						error: function(xhr, status, error) {
							enableButton(button)
							_this.$('[rel=tooltip]').tooltip('hide');
						}
						});

					}
				});
			});
		}

	}
},

selectedContains: function(name) {
	return _.find(this.selectedSnapshots, function(snap) {
		return snap.get('name') == name;
	});
},

addToSelected: function(name) {
	this.selectedSnapshots.push(this.collection.find(function(snap) {
		return snap.get('name') == name;
	}));
},

removeFromSelected: function(name) {
	var i = _.indexOf(_.map(this.selectedSnapshots, function(snap) {
		return snap.get('name');
	}), name);
	this.selectedSnapshots.splice(i,1);
},

cancel: function(event) {
	event.preventDefault();
	this.render();
},

});

// Add pagination
Cocktail.mixin(SnapshotsView, PaginationMixin);

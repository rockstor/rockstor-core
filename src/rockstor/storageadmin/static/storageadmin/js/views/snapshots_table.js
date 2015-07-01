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

SnapshotsTableModule  = RockstorModuleView.extend({
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
	this.template = window.JST.share_snapshots_table_template;
	this.paginationTemplate = window.JST.common_pagination;
	this.addTemplate = window.JST.share_snapshot_add;
	this.module_name = 'snapshots';
	this.share = this.options.share;
	this.snapshots = this.options.snapshots;
	this.collection = this.options.snapshots;
	this.collection.on("reset", this.render, this);
	this.selectedSnapshots = [];
	this.modify_choices = [
	                       {name: 'yes', value: 'yes'},
	                       {name: 'no', value: 'no'},
	                       ];
	this.parentView = this.options.parentView;
},

render: function() {
	var _this = this;
	$(this.el).empty();
	$(this.el).append(this.template({
		snapshots: this.collection,
		selectedSnapshots: this.selectedSnapshots,
		share: this.share,
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
		modify_choices: this.modify_choices

	}));

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

	this.$('#add-snapshot-form :input').tooltip();
	this.validator = this.$('#add-snapshot-form').validate({
		onfocusout: false,
		onkeyup: false,
		rules: {
		'snapshot-name': 'validateSnapshotName',
	},
	submitHandler: function() {
		var button = _this.$('#js-snapshot-save');
		if (buttonDisabled(button)) return false;
		disableButton(button);
		$.ajax({
		    url: "/api/shares/" + _this.share.get('name') + "/snapshots/" + _this.$('#snapshot-name').val(),
			type: "POST",
			dataType: "json",
			contentType: 'application/json',
			data: JSON.stringify(_this.$('#add-snapshot-form').getJSON()),
			success: function() {
			_this.$('#add-snapshot-form :input').tooltip('hide');
			enableButton(button);
			_this.collection.fetch({
				success: function(collection, response, options) {
				_this.parentView.trigger('snapshotsModified');
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
	var esize = $(event.currentTarget).attr('data-size');
	var share_name = this.share.get("name");
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	if(confirm("Deleting snapshot("+ name +") deletes "+ esize +" of data permanently. Do you really want to delete it?")){
		disableButton(button);
		$.ajax({
			url: "/api/shares/" + share_name + "/snapshots/" + name,
			type: "DELETE",
			success: function() {
			enableButton(button)
			_this.$('[rel=tooltip]').tooltip('hide');
			_this.selectedSnapshots = [];
			_this.collection.fetch({
				success: function(collection, response, options) {
				_this.parentView.trigger('snapshotsModified');
			}
			});
		},
		error: function(xhr, status, error) {
			enableButton(button)
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
	name = $(event.currentTarget).attr('data-name');
	var checked = $(event.currentTarget).prop('checked');
	this.selectSnapshotWithName(name, checked);
},

selectSnapshotWithName: function(name, checked) {
	if (checked) {
		if (!RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
			RockstorUtil.addToList(
					this.selectedSnapshots, this.collection, 'name', name);
		}
	} else {
		if (RockstorUtil.listContains(this.selectedSnapshots, 'name', name)) {
			RockstorUtil.removeFromList(this.selectedSnapshots, 'name', name);
		}
	}
},

selectAllSnapshots: function(event) {
	var _this = this;
	var checked = $(event.currentTarget).prop('checked');
	this.$('.js-snapshot-select').prop('checked', checked)
	this.$('.js-snapshot-select').each(function() {
		_this.selectSnapshotWithName($(this).attr('data-name'), checked);
	});
},

deleteMultipleSnapshots: function(event) {
	var _this = this;
	event.preventDefault();
	var button = $(event.currentTarget);
	if (buttonDisabled(button)) return false;
	var share_name = this.share.get("name");
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
			$.ajax({
				url: "/api/shares/" + share_name + "/snapshots?id=" + snapIds,
				type: "DELETE",
				success: function() {
				enableButton(button)
				_this.$('[rel=tooltip]').tooltip('hide');
				// reset selected snapshots
				_this.selectedSnapshots = [];
				// reset to prev page if not on first page
				// to handle the case of the last page being deleted
				if (_this.collection.pageInfo().prev) {
					_this.collection.prevPage();
				} else {
					_this.collection.fetch({
						success: function(collection, response, options) {
						_this.parentView.trigger('snapshotsModified');
					}
					});
				}
			},
			error: function(xhr, status, error) {
				enableButton(button)
				_this.$('[rel=tooltip]').tooltip('hide');
				_this.selectedSnapshots = [];
				_this.collection.fetch();
			}
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
Cocktail.mixin(SnapshotsTableModule, PaginationMixin);

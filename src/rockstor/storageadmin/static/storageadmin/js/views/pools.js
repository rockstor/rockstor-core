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
	this.template = window.JST.pool_pools;
	this.pools_table_template = window.JST.pool_pools_table;
	this.pagination_template = window.JST.common_pagination;
	this.collection = new PoolCollection();

	this.disks = new DiskCollection();
	this.disks.pageSize = RockStorGlobals.maxPageSize;
	this.dependencies.push(this.disks);
	this.dependencies.push(this.collection);
	this.collection.on("reset", this.renderPools, this);

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

	$(this.el).html(this.template({ collection: this.collection, disks: this.disks,noOfFreeDisks: _.size(freedisks)  }));


	this.$("#pools-table-ph").html(this.pools_table_template({
	    collection: this.collection
	}));
	this.$(".pagination-ph").html(this.pagination_template({
	    collection: this.collection
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
        }
});

// Add pagination
Cocktail.mixin(PoolsView, PaginationMixin);

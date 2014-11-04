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
 * Add Pool View
 */

AddPoolView = Backbone.View.extend({
  events: {
    "click #js-cancel": "cancel"
  },

  initialize: function() {
  
    this.template = window.JST.pool_add_pool_template;
   
    // dont paginate disk selection table for now
    this.pagination_template = window.JST.common_pagination;
    this.collection = new DiskCollection();
    // this.disks.pageSize = RockStorGlobals.maxPageSize;
    this.collection.on("reset", this.renderDisks, this);
  },

  render: function() {
    this.collection.fetch();
    return this;
  },

  renderDisks: function() {
    $(this.el).empty();
    var _this = this;
    //this.disks.fetch({
      //success: function(collection, response) {
        $(_this.el).append(_this.template({disks: _this.collection}));
        var err_msg = 'Incorrect number of disks';
        var raid_err_msg = function() {
          return err_msg;
        }

        $.validator.addMethod('validatePoolName', function(value) {
          var pool_name = $('#pool_name').val();

          if (pool_name == "") {
            err_msg = 'Please enter pool name';
            return false;
          }
          else
            if(pool_name.length >127){
              err_msg = 'Please enter pool name less than 128 characters';
              return false;
            }
            else
              if(/^[A-Za-z][A-Za-z0-9]*$/.test(pool_name) == false){
                err_msg = 'Pool name must be an alphanumeric starting with an alphabet';
                return false;
              }

              return true;
        }, raid_err_msg);


        $.validator.addMethod('validateRaid', function(value) {
          var raid_level = $('#raid_level').val();
          var n = $("input:checked.disk").length;
          if (raid_level == 'single') {
            if (n < 1) {
              err_msg = 'At least one disk must be selected';
              return false;
            }
          } else if (raid_level == 'raid0') {
            if (n < 2) {
              err_msg = 'Raid0 requires at least 2 disks to be selected';
              return false;
            }
          } else if (raid_level == 'raid1') {
            if (n < 2) {
              err_msg = 'Raid1 requires at least 2 disks to be selected';
              return false;
            }
          } else if (raid_level == 'raid5') {
            if (n < 2) {
              err_msg = 'Raid5 requires at least 2 disks to be selected';
              return false;
            }
          } else if (raid_level == 'raid6') {
            if (n < 3) {
              err_msg = 'Raid6 requires at least 3 disks to be selected';
              return false;
            }
          } else if (raid_level == 'raid10') {
            if (n < 4) {
              err_msg = 'Raid10 requires at least 4 disks to be selected';
              return false;
            }
          }
          return true;
        }, raid_err_msg);
        
        
        this.$("#disks-table").tablesorter({
         headers: {
            // assign the first column (we start counting zero)
            0: {
                // disable it by setting the property sorter to false
                sorter: false
            },
            // assign the third column (we start counting zero)
            3: {
                // disable it by setting the property sorter to false
                sorter: false
            }
         }
        });
        
        _this.$(".pagination-ph").html(_this.pagination_template({
        collection: this.collection
       }));
        
        
        this.$('#add-pool-form input').tooltip({placement: 'right'});

        this.$('#raid_level').tooltip({
          html: true,
          placement: 'right',
          title: "Desired RAID level of the pool<br><strong>Single</strong>: No software raid. (Recommended while using hardware raid).<br><strong>Raid0</strong>, <strong>Raid1</strong>, <strong>Raid10</strong>, <strong>Raid5</strong> and <strong>Raid6</strong> are similar to conventional implementations with key differences.<br>See documentation for more information"
        });

        $('#add-pool-form').validate({
          onfocusout: false,
          onkeyup: false,
          rules: {
            pool_name: "validatePoolName",
            raid_level: "validateRaid"
          },

          submitHandler: function() {
            var button = $('#create_pool');
            if (buttonDisabled(button)) return false;
            disableButton(button);
            var pool_name = $('#pool_name').val();
            var raid_level = $('#raid_level').val();
            var disk_names = [];
            var n = $("input:checked.disk").length;
            $("input:checked.disk").each(function(i) {
              if (i < n) {
                disk_names.push($(this).val());
              }
            });

            var jqxhr = $.ajax({
              url: '/api/pools',
              type: 'POST',
              dataType: 'json',
	      contentType: 'application/json',
              data: JSON.stringify({"disks": disk_names, "raid_level": raid_level,
				    "pname": pool_name}),
            });

             jqxhr.done(function() {
                enableButton(button);

                _this.$('#add-pool-form input').tooltip('hide');
                app_router.navigate('pools', {trigger: true})
             });

             jqxhr.fail(function(xhr, status, error) {
               enableButton(button);
             });

          }

        });

    return this;
  },

  cancel: function(event) {
    event.preventDefault();
    this.$('#add-pool-form :input').tooltip('hide');
    app_router.navigate('pools', {trigger: true});
  }
});

// Add pagination
Cocktail.mixin(AddPoolView, PaginationMixin);
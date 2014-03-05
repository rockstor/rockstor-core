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
 * Add Share View 
 */

AddShareView = Backbone.View.extend({
  events: {
    "click #js-cancel": "cancel"
  },

  initialize: function() {
    this.pools = new PoolCollection();
    this.pools.pageSize = RockStorGlobals.maxPageSize;
    this.poolName = this.options.poolName;
  },

  render: function() {
    $(this.el).empty();
    this.template = window.JST.share_add_share_template;
    var _this = this;
    this.pools.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({pools: _this.pools, poolName: _this.poolName}));
        
        $('#add-share-form :input').tooltip({placement: 'right'});
        
        $('#add-share-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
              share_name: 'required',
              share_size: {
                required: true,
                number: true
              },
            },
            errorPlacement: function(error, element) {
              if (element.attr("name") == "share_size") {
                // insert error for share size after the size format field.
                error.insertAfter("#size_format");
              } else {
                error.insertAfter(element);
              }
            },
            
            submitHandler: function() {
              var button = _this.$('#create_share');
              if (buttonDisabled(button)) return false;
              disableButton(button);
              var share_name = $('#share_name').val();
              var pool_name = $('#pool_name').val();
              var size = $('#share_size').val();

              var sizeFormat = $('#size_format').val();
              if(sizeFormat == 'KB'){
                size = size;
              }else if(sizeFormat == 'MB'){
                size = size*1024;	
              }else if(sizeFormat == 'GB'){
                size = size*1024*1024;
              }else if(sizeFormat == 'TB'){
                size = size*1024*1024*1024;
              }

              $.ajax({
                url: "/api/shares",
                type: "POST",
                dataType: "json",
                data: {sname: share_name, "pool": pool_name, "size": size},
                success: function() {
                  enableButton(button);
                  _this.$('#add-share-form :input').tooltip('hide');
                  app_router.navigate('shares', {trigger: true})
                },
                error: function(xhr, status, error) {
                  enableButton(button);
                },
              });
            }
        });
      }
    });
    return this;
  },

  cancel: function(event) {
    event.preventDefault();
    this.$('#add-share-form :input').tooltip('hide');
    app_router.navigate('shares', {trigger: true})
  }

});


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
  initialize: function() {
    this.pools = new PoolCollection();
  },
  render: function() {
    $(this.el).empty();
    this.template = window.JST.share_add_share_template;
    var _this = this;
    this.pools.fetch({
      success: function(collection, response) {
        $(_this.el).append(_this.template({pools: _this.pools}));
        this.$('#create_share').click(function() {
          var button = _this.$('#create_share');
          if (buttonDisabled(button)) return false;
          disableButton(button);
          _this.$('#create_share').data("executing", true);
          _this.$('#create_share').attr("disabled", true);
          var share_name = $('#share_name').val();
          var pool_name = $('#pool_name').val();
          console.log('pool_name is ' + pool_name);
          var size = $('#share_size').val();
          $.ajax({
            url: "/api/shares/"+share_name+"/",
            type: "POST",
            dataType: "json",
            data: {"pool": pool_name, "size": size},
            success: function() {
              enableButton(button);
              app_router.navigate('shares', {trigger: true}) 
            },
            error: function(request, status, error) {
              enableButton(button);
              showError(request.responseText);	
            }
          });

        });
      }
    });
    return this;
  }
});

var addShareView = new AddShareView();

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
 * Pools Table view
 */

PoolsTableView = RockstoreModuleView.extend({
  render: function() {
    this.template = window.JST.pool_pools_table_template;
    var _this = this;
    $(this.el).empty();
    $(this.el).append(this.template({pools: this.collection}));
    this.$('#pools-table').tablesorter();
    this.$('button[data-action=delete]').click(function(event) {
      var button = _this.$('button[data-action=delete]');
      if (buttonDisabled(button)) return false;
      disableButton(button);
      name = $(event.target).attr('data-name');
      $.ajax({
        url: "/api/pools/" + name + "/",
        type: "DELETE",
        dataType: "json",
        data: { "name": name, "disks": "foo", "raid_level": "foo" }
      }).done(function() {
        _this.collection.fetch();
      }).fail(function(request, status, error) {
        showError(request.responseText); 
      }).always(function() {
        enableButton(button);
      });
    });
    return this;
  }
});

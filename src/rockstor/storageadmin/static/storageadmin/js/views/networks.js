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

/* Services */

NetworksView = Backbone.View.extend({

  initialize: function() {
    this.template = window.JST.network_networks;
    this.collection = new NetworkInterfaceCollection();
    this.paginationTemplate = window.JST.common_pagination;
    this.collection.on('reset', this.renderNetworks, this);
  },

  render: function() {
    var _this = this;
    this.collection.fetch();
    return this;
  },
 
 
  renderNetworks: function() {
    var _this = this;
    $(this.el).empty();
    this.scanNetwork();
    $(this.el).append(this.template({
      networks: this.collection
    }));
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
  },
 
  scanNetwork: function() {
        var _this = this;
        $.ajax({
          url: "/api/network",
          type: "POST",
          dataType: "json",
          success: function(data, status, xhr) {
             _this.collection.fetch();
          },
          error: function(xhr, status, error) {
            logger.debug(error);
          }
        });
      },
 
});

// Add pagination
Cocktail.mixin(NetworksView, PaginationMixin);


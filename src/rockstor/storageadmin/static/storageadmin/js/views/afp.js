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

AFPView  = RockstorLayoutView.extend({
  events: {
    'click .delete-afp-share': 'deleteAFP'
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.afp_afp;
    this.paginationTemplate = window.JST.common_pagination;
    this.module_name = 'afp';
    this.collection = new AFPCollection();
    this.dependencies.push(this.collection);
    this.shares = new ShareCollection();
    // dont paginate shares for now
    this.shares.pageSize = 1000;
    this.dependencies.push(this.shares);
  },

  render: function() {
    var _this = this;
    this.fetch(this.renderAFP, this);
    return this;
  },

  renderAFP: function() {
    this.freeShares = this.shares.reject(function(share) {
      s = this.collection.find(function(afpShare) {
        return (afpShare.get('share') == share.get('name'));
      });
      return !_.isUndefined(s);
    }, this);
    $(this.el).html(this.template({
      collection: this.collection,
      freeShares: this.freeShares
    }));
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));
  },

  deleteAFP: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    if(confirm("Are you sure you want to stop exporting this share via AFP?")){
      disableButton(button)
      var id = $(event.currentTarget).data('id');

      $.ajax({
        url: '/api/netatalk/' + id,
        type: 'DELETE',
        dataType: 'json',
        contentType: 'application/json',
        success: function() {
          _this.render();
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });

    }
  }

});

// Add pagination
//Cocktail.mixin(AFPView, PaginationMixin);

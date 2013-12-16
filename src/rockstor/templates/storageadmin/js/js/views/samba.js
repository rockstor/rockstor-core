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

SambaView  = RockstoreLayoutView.extend({
  events: {
  },
    
  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.template = window.JST.samba_samba;
    this.paginationTemplate = window.JST.common_pagination;
    this.module_name = 'samba';
    this.collection = new SambaCollection();
    this.dependencies.push(this.collection);
  },

  render: function() {
    var _this = this;
    this.fetch(this.renderSamba, this);
    return this;
  },
  
  renderSamba: function() {
    $(this.el).html(this.template({
      collection: this.collection,
    }));
    this.$(".ph-pagination").html(this.paginationTemplate({
      collection: this.collection
    }));

  },

  deleteSambaShare: function(event) {
    var _this = this;
    if (event) event.preventDefault();
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    if(confirm("Delete samba export... Are you sure? ")){
    disableButton(button)
    var id = $(event.currentTarget).data('id');
    $.ajax({
      url: '/api/nfs-exports/' + id,
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
Cocktail.mixin(SambaView, PaginationMixin);


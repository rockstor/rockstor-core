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

DonateView = RockstorLayoutView.extend({

  events: {
      'click #navdonateYes': 'donate',
  },

  initialize: function() {
    // call initialize of base
    this.constructor.__super__.initialize.apply(this, arguments);
   this.template = window.JST.common_navbar;
    this.paginationTemplate = window.JST.common_pagination;
    this.timeLeft = 300;
  },

  render: function() {
    $('#donate-modal').modal('show');
  },

  donate: function() {
    contrib = this.$('input[type="radio"][name="contrib"]:checked').val();
    if (contrib=='custom') {
      contrib = $('#custom-amount').val();
    }
    if (_.isNull(contrib) || _.isEmpty(contrib) || isNaN(contrib)) {
      contrib = 0; // set contrib to 0, let user input the number on paypal
    }
    this.$('input[name="amount"]').val(contrib);
    this.$('#contrib-form').submit()
  },

});

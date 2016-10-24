/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2016 RockStor, Inc. <http://rockstor.com>
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

/* Construct and display a new Bootstrap-styled modal dialog as follows:
 *      var dialog = new ModalView({el: target, template: myTemplate}).render();
 *
 * Manually control the created modal:
 *      dialog.modal(argument);
 *
 * It is only necessary to define the modal-header/body/content divs in the
 * supplied template; the view takes care of the required outer tags.
 */
var ModalView = Backbone.View.extend({
    events: {
        'click [type="submit"]': 'onSubmitClicked'
    },

    initialize: function(options) {
        _.extend(this, options);
    },

    render: function() {
        this.$el.html(window.JST.common_modal_base);
        this.$('.modal-content').html(this.template);
        this.modal('show');
        return this;
    },

    // Propagate submit event
    onSubmitClicked: function() {
        this.trigger('submit');
        this.modal('hide');
    },

    // Proxy the modal dialog method
    modal: function(arg) {
        this.$('.modal').modal(arg);
    }
});



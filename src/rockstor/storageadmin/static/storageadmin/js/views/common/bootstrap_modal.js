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

/* Construct and display a new Bootstrap-styled modal dialog by putting a
 * placeholder target element in your document and attaching the dialog:
 *      var dialog = new ModalView({el: target, template: myTemplate}).render();
 *
 * Manually control the created modal:
 *      dialog.modal(argument);
 *
 * It is only necessary to define the modal-header/body/content divs in the
 * supplied template; the view takes care of the required outer tags.
 * Additionally, the options passed to the constructor are also passed into
 * the template context.
 *
 * Submit events, such as from type="submit" buttons, are re-triggered on the
 * view.
 */
var ModalView = Backbone.View.extend({
    events: {
        'submit': 'onSubmitClicked'
    },

    initialize: function(options) {
        this.options = options || {};
        this.baseTemplate = window.JST.common_modal_base;
    },

    render: function() {
        this.$el.html(this.baseTemplate);
        this.$('.modal-content').html(this.template(this.options));
        this.modal('show');
        return this;
    },

    // Propagate submit event
    onSubmitClicked: function() {
        this.trigger('submit', this);
        this.modal('hide');
    },

    // Proxy the modal dialog method
    modal: function(arg) {
        this.$('.modal').modal(arg);
    }
});

/* The warning dialog has a predefined "Warning" header section and a footer
 * section with Cancel and Confirm buttons. The confirm button triggers a
 * submit event. Pass the body message text on construction:
 *      var warning = new WarningDialog({el: target, message: 'warning'}).render();
 */
var WarningDialog = ModalView.extend({
    initialize: function(options) {
        ModalView.prototype.initialize.call(this, options);
        this.template = window.JST.common_modal_warning;
    }
});

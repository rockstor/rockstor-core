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

// An "outer" view for our forms that embeds the actual form elements in a
// panel view with a title.
FormView = Backbone.View.extend({
    tagName: 'row',

    initialize: function(options) {
        this.template = window.JST.common_form;
        this.form = new Backform.Form(options);
        this.title = options.title;
    },

    render: function() {
        this.$el.html(this.template({title: this.title}));
        this.form.setElement(this.$('form'));
        this.form.render();
        return this;
    }
});

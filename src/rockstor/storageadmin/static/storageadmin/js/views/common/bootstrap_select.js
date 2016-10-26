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

// Internal option view for Select
var SelectOption = Backbone.View.extend({
    tagName: 'option',

    events: {
        'change:selection': 'onSelectionChanged'
    },

    initialize: function(options) {
        this.options = options || {};
    },

    render: function() {
        var content = this.model.get(this.options.attribute) || this.model.id;
        this.$el.html(content);
        return this;
    },

    onSelectionChanged: function() {
        this.model.trigger('change:selection', this.model);
    }
});

// Display a <select> for a Backbone collection. The select option text can be
// set to a model attribute passed in as the 'attribute' option, otherwise it
// displays the model IDs. The currently selected model is available as the
// view's model and a 'change:selection' event is fired by the view when the
// selection changes.
var BootstrapSelect = Backbone.View.extend({
    tagName: 'select',

    className: 'selectpicker',

    attributes: {
        'data-width': 'auto'
    },

    events: {
        'change': 'onSelectionChanged'
    },

    initialize: function(options) {
        this.options = options || {};
        this.listenTo(this.collection, 'update', this.render);
        this.listenTo(this.collection, 'change:selection', this.selectedModel);
    },

    render: function() {
        this.$el.empty();
        this.$el.attr(this.attributes);
        this.collection.each(function(model) {
            var option = new SelectOption(_.extend({model: model}, this.options));
            this.$el.append(option.render().el);
        }, this);
        this.$el.selectpicker('refresh');
        this.onSelectionChanged();
        return this;
    },

    selectedModel: function(model) {
        this.model = model;
        this.trigger('change:selection', model);
    },

    onSelectionChanged: function() {
        this.$(':selected').trigger('change:selection');
    }
});



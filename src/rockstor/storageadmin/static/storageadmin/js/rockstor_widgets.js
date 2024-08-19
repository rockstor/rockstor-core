/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>
 *
 * Rockstor is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published
 * by the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 *
 * Rockstor is distributed in the hope that it will be useful, but
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

RockStorWidgets = {};
RockStorWidgets.max_width = 10;
RockStorWidgets.max_height = 2;

RockStorWidgets.findByName = function(name) {
    return _.find(RockStorWidgets.widgetDefs, function(widget) {
        return widget.name == name;
    });
};

RockStorWidgets.findByCategory = function(category) {
    return _.filter(RockStorWidgets.widgetDefs, function(widget) {
        return widget.category == category;
    });
};

RockStorWidgets.defaultWidgets = function() {
    var tmp = _.filter(RockStorWidgets.widgetDefs, function(widget) {
        return widget.defaultWidget;
    });
    return _.sortBy(tmp, function(w) {
        if (!_.isUndefined(w.position) && !_.isNull(w.position)) {
            return w.position;
        } else {
            return Number.MAX_VALUE;
        }
    });
};

RockStorWidgets.defaultWidgetNames = function(name) {
    return _.map(RockStorWidgets.defaultWidgets(), function(widget) {
        return widget.name;
    });
};

RockStorWidgets.widgetDefs = [];
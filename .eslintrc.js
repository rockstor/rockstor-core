/*
 *
 * @licstart  The following is the entire license notice for the
 * JavaScript code in this page.
 *
 * Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
 *
 */


module.exports = {
    'env': {
        'browser': true,
        'jquery': true,
        'es6': true
    },
    'extends': 'eslint:recommended',
    'rules': {
        'strict': 'off',
        'no-unused-vars': 'off',
        'no-undef': 'off',
        'indent': [
            'error',
            4
        ],
        'linebreak-style': [
            'error',
            'unix'
        ],
        'quotes': [
            'error',
            'single'
        ],
        'semi': [
            'error',
            'always'
        ],
        'no-console': [
            'error',
            {
                'allow': [
                    'log'
                ]
            }
        ]
    },
    'globals': {
        // Rockstor jslibs dependencies
        'Backbone': false,
        'Handlebars': false,
        '_': false,
        'd3': false,
        'humanize': false,
        'io': false,
        'moment': false,
        'Chart': false,
        'options': true
    }
};
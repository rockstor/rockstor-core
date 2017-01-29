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

var gulp = require('gulp');
var eslint = require('gulp-eslint');


gulp.task('lint', lintJob);
gulp.task('default', ['lint']);

function lintJob() {

    var jssrc = 'src/rockstor/storageadmin/static/storageadmin/js/';
    var jsfiles = [
        'license.js',
        'socket_listen.js',
        'rockstor.js',
        'rockstor_widgets.js',
        'rockstor_logger.js',
        'paginated_collection.js',
        'router.js',
        'graph.js',
        'd3.slider2.js',
        'models/models.js',
        'views/common/*.js',
        'views/*.js',
        'views/pool/**/*.js',
        'views/dashboard/*.js'
    ];
    jsfiles = jsfiles.map(function(element) {
        return jssrc + element
    });


    return gulp.src(jsfiles)
        .pipe(eslint('./.eslintrc.js'))
        .pipe(eslint.format())
        .pipe(eslint.failAfterError());
}

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

UsersView = RockstorLayoutView.extend({
    events: {
        'click .delete-user': 'deleteUser',
        'click .edit-user': 'editUser',
        'click .add-pincard': 'addPincard',
        'hidden.bs.modal #pincard-modal': 'PincardModalClose'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.users_users;
        this.collection = new UserCollection();
        this.dependencies.push(this.collection);
        this.collection.on('reset', this.renderUsers, this);
        this.initHandlebarHelpers();
    },

    render: function() {
        this.collection.fetch();
        return this;
    },

    renderUsers: function() {
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }

        this.rockstorUsers = this.collection.filter(function(grp) {
            return (grp.get('admin'));
        });
        this.otherSystemUsers = this.collection.filter(function(grp) {
            return (!grp.get('admin'));
        });

        $(this.el).html(this.template({
            collection: this.collection,
            rockstorUsers: this.rockstorUsers,
            otherSystemUsers: this.otherSystemUsers,
        }));

        this.$('[rel=tooltip]').tooltip({
            placement: 'bottom'
        });
        this.renderDataTables();
    },

    deleteUser: function(event) {
        event.preventDefault();
        var _this = this;
        var username = $(event.currentTarget).attr('data-username');
        if (confirm('Delete user:  ' + username + '. Are you sure?')) {
            $.ajax({
                url: '/api/users/' + username,
                type: 'DELETE',
                dataType: 'json',
                success: function() {
                    _this.collection.fetch();
                },
                error: function(xhr, status, error) {}
            });
        } else {
            return false;
        }
    },

    editUser: function(event) {
        if (event) event.preventDefault();
        if (this.$('[rel=tooltip]')) {
            this.$('[rel=tooltip]').tooltip('hide');
        }
        var username = $(event.currentTarget).attr('data-username');
        app_router.navigate('users/' + username + '/edit', {
            trigger: true
        });
    },

    addPincard: function(event) {
        event.preventDefault();
        var uid = $(event.currentTarget).attr('data-uid');
        var username = $(event.currentTarget).attr('data-username');
        RockStorSocket.pincardManager = io.connect('/pincardmanager', {
            'secure': true,
            'force new connection': true
        });
        $('#pincard_user').text(username);
        RockStorSocket.addListener(this.renderPincard, this, 'pincardManager:newpincard');
        RockStorSocket.pincardManager.emit('generatepincard', uid);
    },

    renderPincard: function(data) {

        //Define start and default values 
        var pins_array = data;
        var pin_cells_start = {
            'x': 7,
            'y': 18
        };
        var pin_cells_dimensions = {
            'x': 45,
            'y': 30
        };
        var pin_indexes_start = {
            'x': 28,
            'y': 15
        };
        var pin_texts_start = {
            'x': 30,
            'y': 38
        };
        var pincard_objects_slide = {
            'x': 53,
            'y': 46
        };
        var Pincard_canvas = $('#Pincard_canvas')[0];
        var ctx = Pincard_canvas.getContext('2d');
        //Clear Pincard canvas
        ctx.clearRect(0, 0, 324, 204);
        //Create canvas shape and fill will black background
        ctx.fillStyle = 'black';
        ctx.strokeStyle = 'black';
        ctx.moveTo(12, 0);
        ctx.lineTo(312, 0);
        ctx.arcTo(324, 0, 324, 12, 12);
        ctx.lineTo(324, 192);
        ctx.arcTo(324, 204, 312, 204, 12);
        ctx.lineTo(12, 204);
        ctx.arcTo(0, 204, 0, 192, 12);
        ctx.lineTo(0, 12);
        ctx.arcTo(0, 0, 12, 0, 12);
        ctx.fill();
        //Add Rockstor watermark image then render pins cells, indexes and pins values
        var background_image = $('#canvas_background')[0];
        //Reduce opacity for background image
        ctx.globalAlpha = 0.3;
        ctx.drawImage(background_image, 32, 2, 260, 208);
        //Back to normal opacity for pin cells, indexes and values
        ctx.globalAlpha = 1;
        ctx.strokeStyle = 'white';
        ctx.lineWidth = '2';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        var pin_index, x_delta, y_delta, pin_cell_x, pin_cell_y,
            pin_index_x, pin_index_y, pin_text_x, pin_text_y;
        var pins_string = '<table class="table table-condensed table-bordered"><tbody>';

        for (var y = 0; y <= 3; y++) {
            //Loop through Pincard rows and calculate y deltas for every object
            y_delta = y * pincard_objects_slide['y'];
            pin_cell_y = pin_cells_start['y'] + y_delta;
            pin_index_y = pin_indexes_start['y'] + y_delta;
            pin_text_y = pin_texts_start['y'] + y_delta;
            pins_string += '<tr>';

            for (var x = 0; x <= 5; x++) {
                //Loop through Pincard columns and calculate
                //x deltas for every object and current pin index value
                pin_index = (x + 1) + y * 6;
                x_delta = x * pincard_objects_slide['x'];
                pin_cell_x = pin_cells_start['x'] + x_delta;
                pin_index_x = pin_indexes_start['x'] + x_delta;
                pin_text_x = pin_texts_start['x'] + x_delta;
                //Render Pin cell
                ctx.strokeRect(pin_cell_x, pin_cell_y, pin_cells_dimensions.x, pin_cells_dimensions.y);
                //Render Pin index
                ctx.font = 'bold 13px Courier New';
                ctx.fillText(pin_index, pin_index_x, pin_index_y);
                //Render Pin value
                ctx.font = 'bold 14px Courier New';
                ctx.fillText(pins_array[pin_index - 1], pin_text_x, pin_text_y);
                pins_string += '<td>' + $('<div/>').text(pins_array[pin_index - 1]).html() + '</td>';
            }
            pins_string += '</tr>';
        }
        pins_string += '</tbody></table>';
        $('#pins_list').html('Selectable Pincard pins:<br/>' + pins_string);
        $('#pincard-modal').modal({
            keyboard: false,
            show: false,
            backdrop: 'static'
        });
        $('#pincard-modal').modal('show');
    },

    PincardModalClose: function() {

        RockStorSocket.removeOneListener('pincardManager');
        RockStorSocket.pincardManager.disconnect();
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_users_table', function(adminBool) {
            var html = '';
            var filteredCollection = null;
            if (adminBool) {
                filteredCollection = this.rockstorUsers;
            } else {
                filteredCollection = this.otherSystemUsers;
            }
            if (filteredCollection == null) {
                html += 'No groups exist';
            } else {
                for (var i = 0; i < filteredCollection.length; i++) {
                    var has_pincard = filteredCollection[i].get('has_pincard');
                    var pincard_allowed = filteredCollection[i].get('pincard_allowed');

                    html += '<tr>';
                    html += '<td><i class="glyphicon glyphicon-user"></i> ' + filteredCollection[i].get('username') + '</td>';
                    html += '<td>' + filteredCollection[i].get('uid') + '</td>';
                    html += '<td>' + filteredCollection[i].get('groupname') + '</td>';
                    html += '<td>' + filteredCollection[i].get('gid') + '</td>';
                    html += '<td>';
                    if (filteredCollection[i].get('shell') != null) {
                        html += filteredCollection[i].get('shell');
                    }
                    html += '</td>';
                    html += '<td>';
                    if (filteredCollection[i].get('managed_user')) {
                        html += '<a href="#" class="edit-user" data-username="' + filteredCollection[i].get('username') + '" rel="tooltip" title="Edit user"><i class="glyphicon glyphicon-pencil"></i></a>&nbsp;';
                        html += '<a href="#" class="delete-user" data-username="' + filteredCollection[i].get('username') + '" rel="tooltip" title="Delete user"><i class="glyphicon glyphicon-trash"></i></a>&nbsp;';
                    }
                    if (has_pincard && pincard_allowed == 'yes') {
                        html += '<a href="#" class="add-pincard" data-username="' + filteredCollection[i].get('username') + '" data-uid="' + filteredCollection[i].get('uid') + '" rel="tooltip" title="Pincard already present - Click to generate a new Pincard"><i class="fa fa-credit-card text-success" aria-hidden="true"></i></a>';
                    } else {
                        switch (pincard_allowed) {
                        case 'yes':
                            html += '<a href="#" class="add-pincard" data-username="' + filteredCollection[i].get('username') + '" data-uid="' + filteredCollection[i].get('uid') + '" rel="tooltip" title="Click to generate a new Pincard"><i class="fa fa-credit-card text-success" aria-hidden="true"></i></a>';
                            break;
                        case 'otp':
                            html += '<a href="#email" rel="tooltip" title="Pincard+OTP (One Time Password) via mail required, Email Alerts not enabled, click to procede"><i class="fa fa-credit-card text-warning" aria-hidden="true"></i></a>';
                            break;
                        }
                    }
                    html += '</td>';
                    html += '</tr>';
                }
            }
            return new Handlebars.SafeString(html);
        });
    }

});
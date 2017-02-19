/*
 *
 * @licstart  The following is the entire license notice for the 
 * JavaScript code in this page.
 * 
 * Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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


AddAccessKeyView = RockstorLayoutView.extend({
    events: {
        'click #js-cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.access_keys_add_access_key;
    },

    render: function() {
        var _this = this;
        $(this.el).html(this.template());
        this.$('#add-access-key-form :input').tooltip({
            placement: 'right'
        });
        this.$('#add-access-key-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                access_key_name: 'required',
            },
            submitHandler: function() {
                var button = _this.$('#create-access-key');
                if (buttonDisabled(button)) return false;
                var name = _this.$('#name').val();
                disableButton(button);
                $.ajax({
                    url: '/api/oauth_app',
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        name: name
                    },
                    success: function() {
                        enableButton(button);
                        _this.$('#add-access-key-form :input').tooltip('hide');
                        app_router.navigate('access-keys', {
                            trigger: true
                        });
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                    },
                });
            }
        });
        return this;
    },

    cancel: function(event) {
        event.preventDefault();
        this.$('#add-access-key-form :input').tooltip('hide');
        app_router.navigate('access-keys', {
            trigger: true
        });
    }

});
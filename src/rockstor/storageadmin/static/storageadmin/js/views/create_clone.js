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

CreateCloneView = RockstorLayoutView.extend({
    events: {
        'click #js-cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.share_create_clone;
        this.sourceType = this.options.sourceType;
        this.shareId = this.options.shareId;
        this.snapName = this.options.snapName;

        this.share = new Share({
            sid: this.shareId
        });
        this.dependencies.push(this.share);
    },

    render: function() {
        this.fetch(this.renderSubViews, this);
        return this;
    },

    renderSubViews: function() {
        var _this = this,
            sourceTypeIsShare = false;
        if (this.sourceType == 'share') {
            sourceTypeIsShare = true;
        }
        $(this.el).html(this.template({
            sourceType: this.sourceType,
            shareName: this.share.get('name'),
            snapName: this.snapName,
            sourceTypeIsShare: sourceTypeIsShare
        }));
        this.$('#create-clone-form :input').tooltip();
        this.$('#create-clone-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {
                name: 'required'
            },
            submitHandler: function() {
                var button = _this.$('#create-clone');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var url;
                if (_this.sourceType == 'share') {
                    url = '/api/shares/' + _this.shareId + '/clone';
                } else if (_this.sourceType == 'snapshot') {
                    url = '/api/shares/' + _this.shareId + '/snapshots/' +
                        _this.snapName + '/clone';
                }
                $.ajax({
                    url: url,
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#create-clone-form').getJSON()),
                    success: function() {
                        enableButton(button);
                        app_router.navigate('shares', {
                            trigger: true
                        });
                    },
                    error: function(xhr, status, error) {
                        enableButton(button);
                    }
                });
                return false;
            }
        });
        return this;
    },

    cancel: function(event) {
        event.preventDefault();
        if (this.sourceType == 'share') {
            app_router.navigate('#shares/' + this.shareId, {
                trigger: true
            });
        } else if (this.sourceType == 'snapshot') {
            app_router.navigate('#shares/' + this.shareId, {
                trigger: true
            });
        }
    }

});

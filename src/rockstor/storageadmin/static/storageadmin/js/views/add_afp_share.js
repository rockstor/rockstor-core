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

AddAFPShareView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.afp_add_afp_share;
        this.shares = new ShareCollection();
        // dont paginate shares for now
        this.shares.pageSize = RockStorGlobals.maxPageSize;
        this.dependencies.push(this.shares);
        this.afpShareId = this.options.afpShareId || null;
        this.afpShares = new AFPCollection({
            afpShareId: this.afpShareId
        });
        this.dependencies.push(this.afpShares);
        this.yes_no_choices = [{
            name: 'yes',
            value: 'yes'
        },
        {
            name: 'no',
            value: 'no'
        },
        ];
        this.time_machine_choices = this.yes_no_choices;
        this.initHandlebarHelpers();
    },

    render: function() {
        this.fetch(this.renderAFPForm, this);
        return this;
    },

    renderAFPForm: function() {
        var _this = this;
        var afpShareIdNotNull = false; //afpShareId is Null by default.
        this.freeShares = this.shares.reject(function(share) {
            s = this.afpShares.find(function(afpShare) {
                return (afpShare.get('share') == share.get('name'));
            });
            return !_.isUndefined(s);
        }, this);

        if (this.afpShareId != null) {
            this.aShares = this.afpShares.get(this.afpShareId);
            afpShareIdNotNull = true;
        } else {
            this.aShares = null;
        }

        $(this.el).html(this.template({
            freeShares: this.freeShares,
            afpShare: this.aShares,
            afpShareId: this.afpShareId,
            afpShareIdNotNull: afpShareIdNotNull,
            time_machine_choices: this.time_machine_choices,
        }));

        $('#add-afp-share-form :input').tooltip({
            html: true,
            placement: 'right'
        });

        this.$('#shares').select2();


        $.validator.setDefaults({
            ignore: ':hidden:not(select)'
        });

        $('#add-afp-share-form').validate({
            onfocusout: false,
            onkeyup: false,
            rules: {

                shares: 'required',

            },

            submitHandler: function() {
                var button = $('#create-afp-export');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                var submitmethod = 'POST';
                var posturl = '/api/netatalk';
                if (_this.afpShareId != null) {
                    submitmethod = 'PUT';
                    posturl += '/' + _this.afpShareId;
                }
                $.ajax({
                    url: posturl,
                    type: submitmethod,
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(_this.$('#add-afp-share-form').getJSON()),
                    success: function() {
                        enableButton(button);
                        _this.$('#add-afp-share-form :input').tooltip('hide');
                        app_router.navigate('afp', {
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
    },

    cancel: function(event) {
        event.preventDefault();
        this.$('#add-afp-share-form :input').tooltip('hide');
        app_router.navigate('afp', {
            trigger: true
        });
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('display_shares_dropdown', function() {
            var html = '';
            if (this.afpShareIdNotNull) {
                var afpShare = this.afpShare.get('share');
                html += '<option value="' + afpShare + '" selected="selected">' + afpShare + '</option>';
            } else {
                _.each(this.freeShares, function(share, index) {
                    var shareName = share.get('name');
                    html += '<option value="' + shareName + '">' + shareName + '</option>';
                });
            }
            return new Handlebars.SafeString(html);
        });

        Handlebars.registerHelper('display_timeMachine_choices', function() {
            var html = '';
            _.each(this.time_machine_choices, function(c) {
                var choiceName = c.name,
                    choiceValue = c.value;
                html += '<label class="radio-inline">';
                if (this.afpShareIdNotNull) {
                    if (choiceValue == afpShare.get('time_machine')) {
                        html += '<input type="radio" name="time_machine" value="' + choiceValue + '" title="Enable Time Machine support for this Share to backup Macs." checked> ' + choiceName;
                    } else {
                        html += '<input type="radio" name="time_machine" value="' + choiceValue + '" title="Don\'t enable Time Machine support for this Share." > ' + choiceName;
                    }
                } else {
                    if (choiceValue == 'yes') {
                        html += '<input type="radio" name="time_machine" value="' + choiceValue + '" title="Enable Time Machine support for this Share to backup Macs" checked> ' + choiceName;
                    } else {
                        html += '<input type="radio" name="time_machine" value="' + choiceValue + '" title="Don\'t enable Time Machine support for this Share." > ' + choiceName;
                    }
                }
                html += '</label>';
            });
            return new Handlebars.SafeString(html);
        });
    }

});
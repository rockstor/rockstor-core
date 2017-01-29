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

NFSAdvancedEditView = RockstorLayoutView.extend({
    events: {
        'click #cancel': 'cancel'
    },

    initialize: function() {
        this.constructor.__super__.initialize.apply(this, arguments);
        this.template = window.JST.nfs_advanced_edit;
        this.collection = new AdvancedNFSExportCollection();
        this.dependencies.push(this.collection);
    },

    render: function() {
        this.fetch(this.renderAdvancedEdit, this);
        return this;
    },

    renderAdvancedEdit: function() {
        var _this = this;
        var ro_str = '';
        var rw_str = '';

        this.collection.each(function(nfsExport) {
            var prefix = 'Normally added -- ';
            var n = prefix.length;
            var s = nfsExport.get('export_str');
            if (s.indexOf(prefix) == 0) {
                ro_str = ro_str + s.substring(n, s.length) + '\n';
            } else {
                rw_str = rw_str + s + '\n';
            }
        });
        $(this.el).html(this.template({
            shares: this.shares,
            collection: this.collection,
            ro_str: ro_str,
            rw_str: rw_str
        }));
        $('#advanced-edit-form').validate({
            onfocusout: false,
            onkeyup: false,

            submitHandler: function() {
                var button = $('#submit-advanced-edit');
                var nfsText = _this.$('#nfs-text').val();
                var entries = [];
                if (!_.isNull(nfsText) && nfsText.trim() != '') entries = nfsText.trim().split('\n');
                if (buttonDisabled(button)) return false;
                disableButton(button);
                $.ajax({
                    url: '/api/adv-nfs-exports',
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        entries: entries
                    }),
                    success: function() {
                        enableButton(button);
                        app_router.navigate('nfs-exports', {
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
        app_router.navigate('nfs-exports', {
            trigger: true
        });
    }

});
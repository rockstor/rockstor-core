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

/*
 * Add Share View
 */

AddShareView = Backbone.View.extend({
    events: {
        'click #js-cancel': 'cancel'
    },

    initialize: function() {
        var _this = this;
        this.pools = new PoolCollection();
        this.pools.pageSize = RockStorGlobals.maxPageSize;
        this.preSelectedPoolName = this.options.poolName || null;
        this.tickFormatter = function(d) {
            var formatter = d3.format(',.1f');
            if (d > 1024) {
                return formatter(d / (1024)) + ' TB';
            } else {
                return formatter(d) + ' GB';
            }
        };
        this.slider = null;
        this.sliderCallback = function(slider) {
            var value = slider.value();
            _this.$('#share_size').val(_this.tickFormatter(value));
        };
        this.initHandlebarHelpers();
    },

    render: function() {
        $(this.el).empty();
        this.template = window.JST.share_add_share_template;
        var _this = this;
        this.pools.fetch({
            success: function(collection, response) {
                $(_this.el).append(_this.template({
                    pools: _this.pools,
                    poolName: _this.poolName
                }));

                var err_msg = '';
                var name_err_msg = function() {
                    return err_msg;
                };

                $.validator.addMethod('validateShareName', function(value) {
                    var share_name = $('#share_name').val();
                    if (/^[A-Za-z0-9_.-]+$/.test(share_name) == false) {
                        err_msg = 'Please enter a valid share name ';
                        return false;
                    }
                    return true;
                }, name_err_msg);

                _this.renderSlider();
                _this.$('#pool_name').change(function() {
                    _this.renderSlider();
                    _this.$('#share_size').val(_this.tickFormatter(1));
                });


                _this.$('#share_size').val(_this.tickFormatter(1));
                _this.$('#share_size').change(function() {
                    var size = this.value;
                    var size_value = size;

                    var sizeFormat = size.replace(/[^a-z]/gi, '');
                    if (sizeFormat != '') {
                        var size_array = size.split(sizeFormat);
                        size_value = size_array[0];
                    }

                    if (sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb') {
                        size_value = size_value * 1024;
                        _this.slider.setValue((size_value) * 1024);
                    } else if (sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb') {
                        _this.slider.setValue((size_value));
                    } else {
                        _this.slider.setValue((size_value));
                    }
                });



                $('#add-share-form input').tooltip({
                    placement: 'right'
                });

                _this.$('#compression').tooltip({
                    html: true,
                    placement: 'right',
                    title: 'Choose a compression algorithm for this Share. By default, parent pool\'s compression algorithm is applied.<br> If you like to set pool wide compression, don\'t choose anything here. If you want finer control of this particular Share\'s compression algorithm, you can set it here.<br><strong>zlib: </strong>slower than lzo but higher compression ratio.<br><strong>lzo: </strong>faster than zlib but lower compression ratio.'
                });

                $('#add-share-form').validate({
                    onfocusout: false,
                    onkeyup: false,
                    rules: {
                        share_name: 'validateShareName',
                        share_size: {
                            required: true
                        },
                    },

                    submitHandler: function() {
                        var button = _this.$('#create_share');
                        if (buttonDisabled(button)) return false;
                        disableButton(button);
                        var share_name = $('#share_name').val();
                        var pool_name = $('#pool_name').val();
                        var compression = $('#compression').val();
                        if (compression == 'no') {
                            compression = null;
                        }
                        var size = $('#share_size').val();
                        var sizeFormat = size.replace(/[^a-z]/gi, '');
                        var size_array = size.split(sizeFormat);
                        //New size_value replace commas granting avoid NaN
                        //and use *1 to number conversion instead of Math.Round
                        //to preserve user defined decimals
                        var size_value = size_array[0].replace(/,/, '') * 1;

                        if (sizeFormat == 'TB' || sizeFormat == 'tb' || sizeFormat == 'Tb') {
                            size_value = size_value * 1024 * 1024 * 1024;
                        } else if (sizeFormat == 'GB' || sizeFormat == 'gb' || sizeFormat == 'Gb') {
                            size_value = size_value * 1024 * 1024;
                        } else {
                            size_value = size_value * 1024 * 1024;
                        }
                        $.ajax({
                            url: '/api/shares',
                            type: 'POST',
                            dataType: 'json',
                            contentType: 'application/json',
                            data: JSON.stringify({
                                sname: share_name,
                                'pool': pool_name,
                                'size': size_value,
                                'compression': compression,
                            }),
                            success: function() {
                                enableButton(button);
                                _this.$('#add-share-form :input').tooltip('hide');
                                app_router.navigate('shares', {
                                    trigger: true
                                });
                            },
                            error: function(xhr, status, error) {
                                enableButton(button);
                                console.log(error);
                            },
                        });
                    }
                });
            }
        });
        return this;
    },

    renderSlider: function() {
        var pool_name = this.$('#pool_name').val();
        var selectedPool = this.pools.find(function(p) {
            return p.get('name') == pool_name;
        });
        //var max = (selectedPool.get('free') + selectedPool.get('reclaimable')) / (1024*1024);
        var min = 0;
        var ticks = 3;
        var value = 1;
        var gb = 1024 * 1024;
        var max = Math.round(selectedPool.get('size') / gb);
        var reclaimable = (selectedPool.get('reclaimable') / gb).toFixed(1);
        var free = (selectedPool.get('free') / gb).toFixed(1);
        var used = ((selectedPool.get('size') -
            selectedPool.get('reclaimable') -
            selectedPool.get('free')) / gb).toFixed(1);

        this.$('#slider').empty();
        this.slider = d3.slider2().min(min).max(max).ticks(ticks).tickFormat(this.tickFormatter).value(value).reclaimable(reclaimable).used(used).callback(this.sliderCallback);
        d3.select('#slider').call(this.slider);
        this.$('#legend-free-num').html('(' + free + ' GB)');
        this.$('#legend-reclaimable-num').html('(' + reclaimable + ' GB)');
        this.$('#legend-used-num').html('(' + used + ' GB)');
    },

    cancel: function(event) {
        event.preventDefault();
        this.$('#add-share-form :input').tooltip('hide');
        app_router.navigate('shares', {
            trigger: true
        });
    },

    initHandlebarHelpers: function() {
        Handlebars.registerHelper('print_pool_names', function() {
            var html = '';
            if (this.preSelectedPoolName) {
                this.pools.each(function(pool, index) {
                    var poolName = pool.get('name');
                    if (preSelectedPoolName != pool.get('name')) {
                        html += '<option value="' + poolName + '">' + poolName + '</option>';
                    } else {
                        html += '<option value="' + preSelectedPoolName + '" selected="selected">' + preSelectedPoolName + '</option>';
                    }
                });
            } else {
                this.pools.each(function(pool, index) {
                    var poolName = pool.get('name');
                    //the pool with index zero is selected by default
                    if (index == 0) {
                        html += '<option value="' + poolName + '" selected="selected">' + poolName + '</option>';
                    } else {
                        html += '<option value="' + poolName + '">' + poolName + '</option>';
                    }
                });
            }
            return new Handlebars.SafeString(html);
        });

    }

});
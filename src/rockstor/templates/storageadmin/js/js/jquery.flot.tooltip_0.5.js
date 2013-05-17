/*
 * jquery.flot.tooltip
 *
 * desc:	create tooltip with values of hovered point on the graph, 
			support many series, time mode, stacking
			you can set custom tip content (also with use of HTML tags) and precision of values
 * version:	0.4.4
 * author: 	Krzysztof Urbas @krzysu [myviews.pl]
 * modify:  SKELETON9@9#, https://github.com/skeleton9/flot.tooltip
 * website:	https://github.com/krzysu/flot.tooltip
 * 
 * released under MIT License, 2012
*/

(function ($) {
    var options = {
		tooltip: false, //boolean
		tooltipOpts: {
			content: "%s | X: %x | Y: %y.2", //%s -> series label, %x -> X value, %y -> Y value, %x.2 -> precision of X value, %p.2 -> percentage of pie or stacked with precision
			dateFormat: "%y-%0m-%0d",
			shifts: {
				x: 10,
				y: 20
			},
			defaultTheme: true,
			labelRegex: null      //use regex to process label
		}
	};
	
    var init = function(plot) {
		var adjustLabel = null;
		var tipPosition = {x: 0, y: 0};
		var opts = plot.getOptions();
		var processed = false;
		var stackSums = {};
		
		var updateTooltipPosition = function(pos) {
			tipPosition.x = pos.x;
			tipPosition.y = pos.y;
		};
		
		var onMouseMove = function(e) {
            
			var pos = {x: 0, y: 0};
			pos.x = e.pageX;
			pos.y = e.pageY;
			
			updateTooltipPosition(pos);
        };
		
		var timestampToDate = function(tmst) {

			var theDate = new Date(tmst);
			
			return $.plot.formatDate(theDate, opts.tooltipOpts.dateFormat);
		};
		
		plot.hooks.processOptions.push(function(plot, options)
		{
			if(options.tooltipOpts.labelRegex)
			{
				adjustLabel = options.tooltipOpts.labelRegex;
			}
			if(options.series.stack) // support percentage for stacked chart, add by skeleton9
			{
				plot.hooks.processRawData.push(processRawData);
			}
		});
		
		plot.hooks.bindEvents.push(function (plot, eventHolder) {
            
			var to = opts.tooltipOpts;
			var placeholder = plot.getPlaceholder();
			var $tip;
			
			if (opts.tooltip === false) return;

			if( $('#flotTip').length > 0 ){
				$tip = $('#flotTip');
			}
			else {
				$tip = $('<div />').attr('id', 'flotTip');
				$tip.appendTo('body').hide().css({position: 'absolute'});
			
				if(to.defaultTheme) {
					$tip.css({
						'background': '#fff',
						'z-index': '10000',
						'padding': '0.4em 0.6em',
						'border-radius': '0.5em',
						'font-size': '0.8em',
						'border': '1px solid #111'
					});
				}
			}
			
			$(placeholder).bind("plothover", function (event, pos, item) {
				if (item) {					
					var tipText;

					if(opts.xaxis.mode === "time" || opts.xaxes[0].mode === "time") {
						tipText = stringFormat(to.content, item, timestampToDate);
					}
					else {
						tipText = stringFormat(to.content, item);						
					}
					
					$tip.html( tipText ).css({left: tipPosition.x + to.shifts.x, top: tipPosition.y + to.shifts.y}).show();
				}
				else {
					$tip.hide().html('');
				}
			});
			
            eventHolder.mousemove(onMouseMove);
        });
		
		var stringFormat = function(content, item, fnct) {
			if (item.series.tooltipOpts && item.series.tooltipOpts.content){
				content = item.series.tooltipOpts.content;
			}
			var seriesPattern = /%s/;
			var xPattern = /%x\.{0,1}(\d{0,})/;
			var yPattern = /%y\.{0,1}(\d{0,})/;
			var pPattern = /%p\.{0,1}(\d{0,})/; //add by skeleton9 to support percentage in pie/stacked
			
			//series match
			if( typeof(item.series.label) !== 'undefined' ) {
				var label = item.series.label;
				if(adjustLabel)
				{
					label = label.match(adjustLabel)[0]
				}
				content = content.replace(seriesPattern, label);
			}
			// xVal match
			if( typeof(fnct) === 'function' ) {
				content = content.replace(xPattern, fnct(item.series.data[item.dataIndex][0]) );
			}
			else {
				content = adjustValPrecision(xPattern, content, item.series.data[item.dataIndex][0]);
			}
			// yVal match
			content = adjustValPrecision(yPattern, content, item.series.data[item.dataIndex][1]);
			
			//add by skeleton9 to support percentage in pie
			if(item.series.percent)
			{
				content = adjustValPrecision(pPattern, content, item.series.percent);
			}
			else if(item.series.percents) //support for stacked percentage
			{
				content = adjustValPrecision(pPattern, content, item.series.percents[item.dataIndex])
			}

			return content;
		};
		
		var adjustValPrecision = function(pattern, content, value) {
		
			var precision;
			if( content.match(pattern) !== 'null' ) {
				if(RegExp.$1 !== '') {
					precision = RegExp.$1;
					value = value.toFixed(precision)
				}
				content = content.replace(pattern, value);
			}
		
			return content;
		};
		
		//set percentage for stacked chart
		function processRawData(plot, series, data, datapoints) 
		{	
			if (!processed)
			{
				processed = true;
				stackSums = getStackSums(plot.getData());
			}
			var num = data.length;
			series.percents = [];
			for(var j=0;j<num;j++)
			{
				var sum = stackSums[data[j][0]+""];
				if(sum>0)
				{
					series.percents.push(data[j][1]*100/sum);
				} else {
					series.percents.push(0);
				}
			}
		}
		
		//calculate summary
        function getStackSums(_data) {
            var data_len = _data.length;
            var sums = {};
            if (data_len > 0) {
                //caculate summary
                for (var i = 0; i < data_len; i++) {
                    if (_data[i].stackpercent || _data[i].stack) {
						var key_idx = 0;
						var value_idx = 1;
						if (_data[i].bars && _data[i].bars.horizontal && _data[i].bars.horizontal === true) {
							key_idx = 1;
							value_idx = 0;
						}
                        var num = _data[i].data.length;
                        for (var j = 0; j < num; j++) {
                            var value = 0;
                            if (_data[i].data[j][1] != null) {
                                value = _data[i].data[j][value_idx];
                            }
                            if (sums[_data[i].data[j][key_idx] + ""]) {
                                sums[_data[i].data[j][key_idx] + ""] += value;
                            } else {
                                sums[_data[i].data[j][key_idx] + ""] = value;
                            }

                        }
                    }
                }
            }
            return sums;
        }
    }
    
    $.plot.plugins.push({
        init: init,
        options: options,
        name: 'tooltip',
        version: '0.5'
    });
})(jQuery);

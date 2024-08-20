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

function displayUsagePieChart(svg, outerRadius, innerRadius, w, h, dataset, dataLabels, total) {

    var arc = d3.svg.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    var pie = d3.layout.pie();

    //var colors = {
    //free: {fill: 'rgb(21,130,61)', stroke: 'rgb(255,255,255)'}, 
    //used: {fill: 'rgb(122,122,122)', stroke: 'rgb(255,255,255)'}
    //};
    var colors = {
        used: {
            fill: 'rgb(128,128,128)',
            stroke: 'rgb(221,221,221)'
        },
        free: {
            fill: 'rgb(168,247,171)',
            stroke: 'rgb(221,221,221)'
        },
    };

    total = _.reduce(dataset, function(t, s) {
        return t + s;
    }, 0);

    //Set up groups
    var arcs = svg.selectAll('g.arc')
        .data(pie(dataset))
        .enter()
        .append('g')
        .attr('class', 'arc')
        .attr('transform', 'translate(' + (outerRadius + 5) + ', ' + (outerRadius + 5) + ')');

    //Draw arc paths
    arcs.append('path')
        .attr('fill', function(d, i) {
            return colors[dataLabels[i]].fill;
        })
        .attr('stroke', function(d, i) {
            return colors[dataLabels[i]].stroke;
        })
        .attr('stroke-width', 1)
        .attr('class', 'pie')
        .attr('d', arc);

    //Labels
    //arcs.append('text')
    //.attr('transform', function(d) {
    //return 'translate(' + arc.centroid(d) + ')';
    //})
    //.attr('text-anchor', 'middle')
    //.attr('class', 'pie')
    //.text(function(d, i) {
    //return d.value; 
    //});

    var labels = svg.selectAll('g.labels')
        .data(dataLabels)
        .enter()
        .append('g')
        .attr('transform', function(d, i) {
            return 'translate(' + (5 + (outerRadius * 2) + 50) + ',' + (5 + i * 25) + ')';
        });

    labels.append('rect')
        .attr('width', 13)
        .attr('height', 13)
        .attr('fill', function(d, i) {
            return colors[d].fill;
        })
        .attr('stroke', function(d, i) {
            return colors[d].stroke;
        });


    labels.append('text')
        .attr('text-anchor', 'left')
        .attr('class', 'legend')
        .attr('transform', function(d, i) {
            return 'translate(16,13)';
        })
        .text(function(d, i) {
            percent = Math.round((dataset[i] / total) * 100);
            return 'Space ' + d + ' - ' + humanize.filesize(dataset[i]);
        });

    var sizeLabel = svg.selectAll('g.sizeLabel')
        .data([total])
        .enter()
        .append('g')
        .attr('transform', function(d, i) {
            return 'translate(5,' + (5 + outerRadius * 2 + 20) + ')';
        });

    sizeLabel.append('text')
        .attr('text-anchor', 'left')
        .text(function(d) {
            return 'Size ' + humanize.filesize(d);
        });

}
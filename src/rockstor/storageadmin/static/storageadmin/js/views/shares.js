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
 * Shares View
 */

SharesView = RockstorLayoutView.extend({
  events: {
    "click a[data-action=delete]": "deleteShare",
    'click #js-cancel': 'cancel',
    'click #js-confirm-share-delete': 'confirmShareDelete'
  },

  initialize: function() {
    this.constructor.__super__.initialize.apply(this, arguments);

    this.template = window.JST.share_shares;
    this.shares_table_template = window.JST.share_shares_table;

    this.pools = new PoolCollection();
    this.collection = new ShareCollection();
    this.dependencies.push(this.pools);
    this.dependencies.push(this.collection);

    this.pools.on("reset", this.renderShares, this);
    this.collection.on("reset", this.renderShares, this);

    Handlebars.registerPartial('pagination',
    '{{test_helper}}'
    );

    Handlebars.registerHelper('test_helper', function() {

      var totalPageCount = this.collection.pageInfo().num_pages,
          currPageNumber = this.collection.pageInfo().page_number,
          maxEntriesPerPage = this.collection.pageSize,
          totalEntryCount = this.collection.count,
          pagePrev = this.collection.pageInfo().prev,
          pageNext = this.collection.pageInfo().next,
          backwardIcon = '<i class="glyphicon glyphicon-backward"></i>',
          fastBackwardIcon = '<i class="glyphicon glyphicon-fast-backward"></i>',
          forwardIcon = '<i class="glyphicon glyphicon-forward"></i>',
          fastForwardIcon = '<i class="glyphicon glyphicon-fast-forward"></i>'
          html = '',
          entries = currPageNumber * maxEntriesPerPage,
          entry_prefix = 0;

          if (totalPageCount > 1) {
            html += '<nav>';
            if(currPageNumber * maxEntriesPerPage > totalEntryCount){
              entries = totalEntryCount;
            }
            entry_prefix = (currPageNumber - 1) * (maxEntriesPerPage) + 1 ;

            html += '<p><i>Displaying entries ' + entry_prefix + ' - ' + (entries) + ' of ' + totalEntryCount + '</i></p>';
            html += '<ul class="pagination">';
            html += '<li><a class="go-to-page" href="#" data-page="1">' + fastBackwardIcon + '</a></li>';
            if (pagePrev) {
              html += '<li><a class="prev-page" href="#">' + backwardIcon + '</a></li>';
            } else {
              html += '<li class="disabled"><a class="prev-page" href="#">' + backwardIcon + '</a></li>';
            }

            var start = currPageNumber - 4 ;
            if(start <= 0){
              start = 1;
            }
            var end = start + 9;
            if(end > totalPageCount){
              end = totalPageCount;
            }
            for (var i=start; i<= end; i++) {
              if (i == currPageNumber) {
                  html += '<li class="active"><a class="go-to-page" href="#" data-page="' + i + '">' + i + '</a></li>';
              } else {
                  html += '<li><a class="go-to-page" href="#" data-page="' + i + '">' + i + '</a></li>';
              }
            }
            if (pageNext) {
                html += '<li><a class="next-page" href="#">' + fastForwardIcon + '</a></li>';
            } else {
                html += '<li class="disabled"><a class="next-page" href="#">' + forwardIcon + '</a></li>';
            }
              html += '<li><a class="go-to-page" href="#" data-page="' + totalPageCount + '">'+ fastForwardIcon +'</a></li>';
              html += '</ul>';
              html += '</nav>';
         }

        return new Handlebars.SafeString(html);
    });

    Handlebars.registerHelper('print_tbody', function() {
      var html = '';
      this.collection.each(function(share, index) {
          var shareName = share.get('name'),
              shareSize = humanize.filesize(share.get('size')*1024),
              shareUsage = humanize.filesize(share.get('rusage')*1024),
              poolName = share.get('pool').name,
              shareCompression = share.get('compression_algo'),
              folderIcon = '<i class="glyphicon glyphicon-folder-open"></i>  ',
              editIcon = '<i class="glyphicon glyphicon-pencil"></i>',
              trashIcon = '<i class="glyphicon glyphicon-trash"></i>';
          html += '<tr>';
          html += '<td><a href="#shares/' + shareName + '">' + folderIcon + shareName +'</a></td>';
          html += '<td>'+ shareSize +'</td>';
          html += '<td>'+ poolName +'</td>';
          html += '<td>'+ shareUsage +'</td>';
          html += '<td>';
          if (shareCompression && shareCompression != 'no') {
              html += shareCompression;
          }else{
              html += 'None(defaults to pool level compression, if any)   ' +
               '<a href="#shares/' + shareName + '/?cView=edit">' + editIcon + '</a>';
          }
          html += '</td>';
          html += '<td><a id="delete_share_' + shareName + '" data-name="' + shareName + '" data-action="delete"' +
          'data-pool="' + poolName + '" data-size="' + shareSize + '" rel="tooltip" title="Delete share">' + trashIcon + '</a></td>';
          html += '</tr>';
      });

      return new Handlebars.SafeString(html);
    });
  },

  render: function() {
    this.fetch(this.renderShares, this);
    return this;
  },

  renderShares: function() {
    if (this.$('[rel=tooltip]')) {
      this.$('[rel=tooltip]').tooltip('hide');
    }
    if (!this.pools.fetched || !this.collection.fetched) {
      return false;
    }
    $(this.el).html(this.template({
      collection: this.collection,
      pools: this.pools
    }));
    this.$("#shares-table-ph").html(this.shares_table_template({
      collection: this.collection,
      collectionNotEmpty: !this.collection.isEmpty(),
      pools: this.pools,
      poolsNotEmpty: !this.pools.isEmpty()
    }));

    this.$("#shares-table").tablesorter({
       headers: {
            // assign the fourth column (we start counting zero)
            4: {
                // disable it by setting the property sorter to false
                sorter: false
            }
         }
    });
    this.$('[rel=tooltip]').tooltip({placement: 'bottom'});
  },

// delete button handler
  deleteShare: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
    shareName = button.attr('data-name');
    // set share name in confirm dialog
    _this.$('#pass-share-name').html(shareName);
    //show the dialog
    _this.$('#delete-share-modal').modal();
    return false;
  },

//modal confirm button handler
  confirmShareDelete: function(event) {
    var _this = this;
    var button = $(event.currentTarget);
    if (buttonDisabled(button)) return false;
        disableButton(button);
      $.ajax({
        url: "/api/shares/" + shareName,
        type: "DELETE",
        dataType: "json",
        success: function() {
          _this.collection.fetch({reset: true});
          enableButton(button);
          _this.$('#delete-share-modal').modal('hide');
          $('.modal-backdrop').remove();
          app_router.navigate('shares', {trigger: true})
        },
        error: function(xhr, status, error) {
          enableButton(button);
        }
      });
    },

    cancel: function(event) {
      if (event) event.preventDefault();
      app_router.navigate('shares', {trigger: true})
    }
});

// Add pagination
Cocktail.mixin(SharesView, PaginationMixin);

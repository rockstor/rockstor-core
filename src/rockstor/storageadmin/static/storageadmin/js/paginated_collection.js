var RockStorPaginatedCollection = Backbone.Collection.extend({

    initialize: function() {
        _.bindAll(this, 'parse', 'url', 'pageInfo', 'nextPage', 'prevPage');
        typeof(options) != 'undefined' || (options = {});
        this.page = 1;
        this.pageSize = RockStorGlobals.maxPageSize;
        this.fetched = false;
    },

    parse: function(resp) {
        this.count = resp.count;
        // fetched is only false if it has never been fetched.
        this.fetched = true;
        return resp.results;
    },

    setPageSize: function(pageSize) {
        this.pageSize = pageSize;
    },

    url: function() {
        if (_.isFunction(this.baseUrl)) {
            return this.baseUrl() + '?' + $.param(this.extraParams());
        }
        return this.baseUrl + '?' + $.param(this.extraParams());
    },

    pageInfo: function() {
        var info = {
            entry_count: this.count, //total number of entries in all pages combined.
            page_number: this.page, //page number of current page
            pageSize: this.pageSize, //maximum number of entries that could be in this page
            num_pages: Math.ceil(this.count / this.pageSize), //total number of pages
            prev: false,
            next: false
        };

        var max = Math.min(this.count, this.page * this.pageSize);

        if (this.total == this.pages * this.pageSize) {
            max = this.total;
        }

        info.range = [(this.page - 1) * this.pageSize + 1, max];

        if (this.page > 1) {
            info.prev = this.page - 1;
        }

        if (this.page < info.pages) {
            info.next = this.page + 1;
        }

        return info;
    },

    nextPage: function() {
        if (!this.pageInfo().next) {
            return false;
        }
        return this.goToPage(this.page + 1);
    },

    prevPage: function() {
        if (!this.pageInfo().prev) {
            return false;
        }
        return this.goToPage(this.page - 1);
    },

    goToPage: function(newPage) {
        this.page = newPage;
        return this.fetch({
            reset: true
        });
    },

    extraParams: function() {
        return {
            page: this.page,
            format: 'json',
            page_size: this.pageSize,
            count: this.count
        };
    }

});
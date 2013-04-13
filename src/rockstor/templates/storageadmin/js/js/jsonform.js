/**
 * @name jsonform.js: for jQuery JsonForm Plugin
 * @description Create standard JSON from Forms or populate form with json using jQuery.
 * @requires jquery.js
 * @link Github: [https://github.com/milfont/jsonform](https://github.com/milfont/jsonform "https://github.com/milfont/jsonform") 
 * @author Christiano Milfont <cmilfont@gmail.com>
 * @license Copyright Milfont Consulting.
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 */
(function ($) {

    /** @memberOf jQuery */
    $.fn.extend({
        /**
         * @version stable
         */
        version: '1.2.5',
        
        /**
         * Example:
         *     $('#form_id').getJSON(true);
         *
         */
         
         /**
         * Example:
         *     $("[name='formname']").getJSON();
         *
         */
         
         /** 
         * @description Create standard JSON from Forms with jQuery. Resolve nested objects.
         *
         * @name getJSON
         * @param {Boolean} byId find inputs with query by id
         * @returns {Object} Object Literal [json]
         * @type jQuery
         * @cat Plugins/jsonform
         */
        getJSON: function(byId) {
            var json = {}, self = this, config;
            if(typeof byId === 'object') {
                config = byId;
                byId = (config.byId)? config.byId : false;
            }
            self.find("input,textarea,select").each( function(index, item) {
                if( !(item.type == "radio" && !item.checked) ) {
                    var name = (byId) ? $.trim(item.id) : $.trim(item.name);
                    var value = (item.type === "select-multiple")? $(item).val() : 
                                                                     item.value;
                    if(name !== "") {
                        if(item.type == "checkbox") {
                          value = (item.checked) ? true : false;
                        }
                        self.merge(json, self.buildJson(name, value, config));
                    }
                }
            });
            return json;
        },
        
        /**
         *
         * Example: with ID for legacy code
         *     var lancamento = {
         *         empresa: {id: 2, name: "Teste"},
         *         partidas: [
         *             {conta: {codigo:"1.02.0002", nome: "Compras"}, natureza: "1"},
         *             {conta: {codigo:"1.02.0001", nome: "Banco"}, natureza: "-1"}
         *         ],
         *         description: "Teste",
         *         value: "125,67",
         *         date: "12/03/1999"
         *     };
         *     $('#form_id').populate(lancamento, true);
         */
         
         /** 
         * Example: with name [default]
         *     var lancamento = {
         *         empresa: {id: 2, name: "Teste"},
         *         partidas: [
         *             {conta: {codigo:"1.02.0002", nome: "Compras"}, natureza: "1"},
         *             {conta: {codigo:"1.02.0001", nome: "Banco"}, natureza: "-1"}
         *         ],
         *         description: "Teste",
         *         value: "125,67",
         *         date: "12/03/1999"
         *     };
         *     $("[name='form_name'").populate(lancamento);
         */
         
         /**
         * @name populate
         * @desc Populate form with json using jQuery. Resolve nested objects. 
         * @param {Object} json Standard JSON to populate FORM
         * @param {Boolean} [optional] byId find inputs with query by id
         * @returns {jQuery} jQuery
         * @type jQuery
         * @cat Plugins/jsonform
         */
        populate: function(json, byId) {

            var eachElementIsNotObject = function(value) {
                return ( value.every(function(val){
                                        return typeof val != "object"; 
                                    })
                        );
            };

            var self = this;
            (function roam(el, father) {
                for(var property in el) {
                    if(el[property] || el[property] === 0) {
                        var value = el[property];
                        if( typeof value == "object" && !($.isArray(value) && eachElementIsNotObject(value) ) ) {
                            var parent = (!father)? property : father + "\\." + property;
                            if($.isArray(value)) {
                                for(var item in value) {
                                    if(value[item]) {
                                        var parent_arr = parent + "\\["+item+"\\]";
                                        roam(value[item], parent_arr);
                                    }
                                }
                            } else {
                                roam(value, parent);
                            }
                            parent = null;
                        } else {
                            var name = (father)? father + "\\." + property : property;
                            var query = "[name='" + name + "']";
                            if(byId) { query = ("#" + name); }
                            
							var other = self.find(query);
                            
                            if(other.length === 0){
                                var selector = query.replace(/\\\[(\d+)?\\\]/g, "\\[\\]"), 
                                    numChave = name.replace(/[^\\\[(\d+)?\\\]]/g, ""), 
                                    index = numChave.replace(/[^\d+]/g, "");
                                
                                other = self.find(selector).eq(index);
                            }
                            
                            other.val(value);
                        }
                    }
                }
            })(json);
            return this;
        },
        /**
         * @name buildJson
         * @param {String} id
         * @param {String} valor
         * @param {Object} config
         * @returns {Object} Object Literal
         */
        buildJson: function(id, valor, config) {
            
            var prefix = (config && config.prefix)? config.prefix:"";
            var suffix = (config && config.suffix)? config.suffix:"";
            
            var verifyArray = function(name, value) {
                var match = name.match(/\[(\d?)\]/);
                if( match ) {
                    var arr = [], position = 0;
                    if(match[1].trim() !== "") {
                        position = match[1];
                    } 
                    arr[ position ] = value;
                    return arr;
                } else {
                    return value;
                }
            };

            return (function generateJSON(json, hierarchyIn, value) {
                var hierarchy = hierarchyIn.split(".");
                var first = hierarchy.shift();
                return function(json, name){
                    json[ prefix + name.replace(/\[(\d?)\]/, "") + suffix ] = (hierarchy.length > 0 ) ? 
                        verifyArray(name, generateJSON({}, hierarchy.join("."), value)) : 
                        verifyArray(name, value);
                    return json;
                }(json, first);
            })({}, id, valor);
        },
        /**
         * @name merge
         * @param {Object} merged
         * @param {Object} source
         * @returns {Object} Object Literal
         */
        merge: (function merge(merged, source) {
            for(var property in source) {
                if(typeof source[property] === 'object' &&
                typeof merged[property] !== "undefined") {
					
                    if($.isArray(merged[property]) && 
                       $.isArray(source[property]) && 
                       !Object.Equals(merged[property], source[property].clean())) {
                        merged[property].push(source[property][0]);
                    } else {
                        merge(merged[property], source[property]);
                    }
                } else {
                    merged[property] = source[property];
                }
            }
            return merged;
        })
    });
	
	Object.Equals = Object.Equals || /*bool*/ function(obj1, obj2){
        return JSON.stringify(obj1) === JSON.stringify(obj2);
    };
	
    Array.prototype.clean = function() {
	  
	  for (var i = 0; i < this.length; i++) {
		if (this[i] === null || this[i] === undefined) {         
		  this.splice(i, 1);
		  i--;
		}
	  }
	  return this;
	};
})(jQuery);
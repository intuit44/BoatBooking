// Polyfill crítico para __extends - Se inyecta al inicio del bundle
(function() {
  'use strict';
  
  if (typeof global === 'undefined') {
    var global = this;
  }
  
  if (typeof global.__extends === 'undefined') {
    global.__extends = function (d, b) {
      if (typeof b !== 'function' && b !== null) {
        throw new TypeError('Class extends value ' + String(b) + ' is not a constructor or null');
      }
      function __() { this.constructor = d; }
      if (b) {
        for (var p in b) if (b.hasOwnProperty && b.hasOwnProperty(p)) d[p] = b[p];
        __.prototype = b.prototype;
        d.prototype = new __();
      } else {
        d.prototype = Object.create(null);
      }
    };
  }
  
  if (typeof global.__assign === 'undefined') {
    global.__assign = Object.assign || function (t) {
      for (var s, i = 1, n = arguments.length; i < n; i++) {
        s = arguments[i];
        for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
          t[p] = s[p];
      }
      return t;
    };
  }
})();
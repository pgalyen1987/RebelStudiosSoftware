/*! Inscrição Estadual validator — Rebel Studios. GPL-3.0-or-later.
 *
 * A direct port of includes/IE.php from Checkout Brasil Pro. The rules come from each state's own
 * page at sintegra.gov.br/Cad_Estados/cad_<UF>.html, read 2026-11-16. tools/ie-parity.mjs checks
 * this file against the 24 worked examples published by the states, the same ones the PHP is
 * tested against, so the two cannot drift apart silently.
 */
(function (root) {
  'use strict';

  var STATES = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
                'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'];

  function digits(v) { return String(v == null ? '' : v).replace(/\D/g, ''); }

  function isExento(v) {
    var s = String(v == null ? '' : v).trim().toUpperCase().replace(/Ç/g, 'C');
    return s === 'ISENTO' || s === 'ISENTA';
  }

  /* Modulus check digit. map overrides a computed digit, e.g. {10:0, 11:0}. */
  function dv(d, weights, mod, map) {
    mod = mod || 11;
    var sum = 0, i;
    for (i = 0; i < weights.length; i++) sum += parseInt(d[i], 10) * weights[i];
    var rest = sum % mod, v = mod - rest;
    if (map && Object.prototype.hasOwnProperty.call(map, v)) return String(map[v]);
    return String(v >= 10 ? 0 : v);
  }

  function sum(d, weights, offset) {
    var s = 0, i;
    for (i = 0; i < weights.length; i++) s += parseInt(d[(offset || 0) + i], 10) * weights[i];
    return s;
  }

  var ZERO = { 10: 0, 11: 0 };

  function simple9(d) {
    if (d.length !== 9) return false;
    return dv(d, [9,8,7,6,5,4,3,2], 11, ZERO) === d[8];
  }

  function prefixed9(d, prefixes) {
    if (d.length !== 9 || prefixes.indexOf(d.slice(0, 2)) === -1) return false;
    return simple9(d);
  }

  var RULES = {
    AC: function (d) {
      if (d.length !== 13 || d.slice(0, 2) !== '01') return false;
      if (dv(d, [4,3,2,9,8,7,6,5,4,3,2], 11, ZERO) !== d[11]) return false;
      return dv(d, [5,4,3,2,9,8,7,6,5,4,3,2], 11, ZERO) === d[12];
    },
    AL: function (d) {
      if (d.length !== 9 || d.slice(0, 2) !== '24') return false;
      if ('03578'.indexOf(d[2]) === -1) return false;
      return String((sum(d, [9,8,7,6,5,4,3,2]) * 10 % 11) % 10) === d[8];
    },
    AP: function (d) {
      if (d.length !== 9 || d.slice(0, 2) !== '03') return false;
      var n = parseInt(d.slice(0, 8), 10), p, dd;
      if (n >= 3000001 && n <= 3017000)      { p = 5; dd = 0; }
      else if (n >= 3017001 && n <= 3019022) { p = 9; dd = 1; }
      else                                   { p = 0; dd = 0; }
      var rest = (p + sum(d, [9,8,7,6,5,4,3,2])) % 11, v = 11 - rest;
      if (v === 10) v = 0;
      if (v === 11) v = dd;
      return String(v) === d[8];
    },
    AM: function (d) {
      if (d.length !== 9) return false;
      var s = sum(d, [9,8,7,6,5,4,3,2]);
      if (s < 11) return String(11 - s) === d[8];
      var rest = s % 11;
      return String(rest <= 1 ? 0 : 11 - rest) === d[8];
    },
    BA: function (d) {
      var len = d.length;
      if (len !== 8 && len !== 9) return false;
      var lead = parseInt(len === 9 ? d[1] : d[0], 10);
      var mod = [0,1,2,3,4,5,8].indexOf(lead) !== -1 ? 10 : 11;
      var body = d.slice(0, len - 2);
      var w2 = len === 9 ? [8,7,6,5,4,3,2] : [7,6,5,4,3,2];
      var r = sum(body, w2) % mod, dv2 = r === 0 ? 0 : mod - r;
      if (dv2 >= 10) dv2 = 0;
      if (String(dv2) !== d[len - 1]) return false;
      var w1 = len === 9 ? [9,8,7,6,5,4,3,2] : [8,7,6,5,4,3,2];
      var r1 = sum(body + dv2, w1) % mod, dv1 = r1 === 0 ? 0 : mod - r1;
      if (dv1 >= 10) dv1 = 0;
      return String(dv1) === d[len - 2];
    },
    CE: simple9,
    DF: function (d) {
      if (d.length !== 13 || d.slice(0, 2) !== '07') return false;
      if (dv(d, [4,3,2,9,8,7,6,5,4,3,2], 11, ZERO) !== d[11]) return false;
      return dv(d, [5,4,3,2,9,8,7,6,5,4,3,2], 11, ZERO) === d[12];
    },
    ES: simple9,
    GO: function (d) {
      if (d.length !== 9) return false;
      var ab = d.slice(0, 2);
      if (ab !== '10' && ab !== '11' && !(ab >= '20' && ab <= '29')) return false;
      var rest = sum(d, [9,8,7,6,5,4,3,2]) % 11, n = parseInt(d.slice(0, 8), 10), v;
      if (rest === 0)      v = 0;
      else if (rest === 1) v = (n >= 10103105 && n <= 10119997) ? 1 : 0;
      else                 v = 11 - rest;
      return String(v) === d[8];
    },
    MA: function (d) { return prefixed9(d, ['12']); },
    MT: function (d) {
      if (d.length !== 11) return false;
      return dv(d, [3,2,9,8,7,6,5,4,3,2], 11, ZERO) === d[10];
    },
    MS: function (d) { return prefixed9(d, ['28','50']); },
    MG: function (d) {
      if (d.length !== 13) return false;
      var s = d.slice(0, 3) + '0' + d.slice(3, 11);
      var w = [1,2,1,2,1,2,1,2,1,2,1,2], cat = '', i;
      for (i = 0; i < 12; i++) cat += String(parseInt(s[i], 10) * w[i]);
      var t = 0;
      for (i = 0; i < cat.length; i++) t += parseInt(cat[i], 10);
      if (String(Math.ceil(t / 10) * 10 - t) !== d[11]) return false;
      return dv(d, [3,2,11,10,9,8,7,6,5,4,3,2], 11, ZERO) === d[12];
    },
    PA: function (d) { return prefixed9(d, ['15','75','76','77','78','79']); },
    PB: simple9,
    PR: function (d) {
      if (d.length !== 10) return false;
      if (dv(d, [3,2,7,6,5,4,3,2], 11, ZERO) !== d[8]) return false;
      return dv(d, [4,3,2,7,6,5,4,3,2], 11, ZERO) === d[9];
    },
    PE: function (d) {
      if (d.length === 14) {
        var v = 11 - (sum(d, [5,4,3,2,1,9,8,7,6,5,4,3,2]) % 11);
        if (v > 9) v -= 10;
        return String(v) === d[13];
      }
      if (d.length !== 9) return false;
      if (dv(d, [8,7,6,5,4,3,2], 11, ZERO) !== d[7]) return false;
      return dv(d, [9,8,7,6,5,4,3,2], 11, ZERO) === d[8];
    },
    PI: simple9,
    RJ: function (d) {
      if (d.length !== 8) return false;
      return dv(d, [2,7,6,5,4,3,2], 11, ZERO) === d[7];
    },
    RN: function (d) {
      var len = d.length;
      if ((len !== 9 && len !== 10) || d.slice(0, 2) !== '20') return false;
      var w = len === 9 ? [9,8,7,6,5,4,3,2] : [10,9,8,7,6,5,4,3,2];
      return String((sum(d, w) * 10 % 11) % 10) === d[len - 1];
    },
    RS: function (d) {
      if (d.length !== 10) return false;
      return dv(d, [2,9,8,7,6,5,4,3,2], 11, ZERO) === d[9];
    },
    RO: function (d) {
      if (d.length !== 14) return false;
      var v = 11 - (sum(d, [6,5,4,3,2,9,8,7,6,5,4,3,2]) % 11);
      if (v >= 10) v -= 10;
      return String(v) === d[13];
    },
    RR: function (d) {
      if (d.length !== 9 || d.slice(0, 2) !== '24') return false;
      return String(sum(d, [1,2,3,4,5,6,7,8]) % 9) === d[8];
    },
    SC: simple9,
    SP: function (d) {
      if (d.length !== 12) return false;
      if (String(sum(d, [1,3,4,5,6,7,8,10]) % 11 % 10) !== d[8]) return false;
      return String(sum(d, [3,2,10,9,8,7,6,5,4,3,2]) % 11 % 10) === d[11];
    },
    SE: simple9,
    TO: function (d) {
      if (d.length !== 11) return false;
      if (['01','02','03','99'].indexOf(d.slice(2, 4)) === -1) return false;
      var body = d.slice(0, 2) + d.slice(4, 10);
      var rest = sum(body, [9,8,7,6,5,4,3,2]) % 11;
      return String(rest < 2 ? 0 : 11 - rest) === d[10];
    }
  };

  function isValid(ie, uf) {
    uf = String(uf == null ? '' : uf).trim().toUpperCase();
    if (STATES.indexOf(uf) === -1) return false;
    if (isExento(ie)) return true;
    var d = digits(ie);
    if (d === '') return false;
    return RULES[uf](d);
  }

  var api = { isValid: isValid, isExento: isExento, digits: digits, STATES: STATES };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IE = api;
})(typeof self !== 'undefined' ? self : this);

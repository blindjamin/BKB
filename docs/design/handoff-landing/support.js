/*
 * support.js — shim local para visualizar BKB-Landing-reference.dc.html
 * fuera de Claude Design. Implementa el subconjunto del runtime que usa
 * la referencia: <x-dc>, <helmet>, <sc-for list as>, {{ expr }},
 * $index, onClick="{{ fn }}", style-hover / style-focus, DCLogic
 * (state, props, setState, renderVals, componentDidMount).
 * Solo para revisión visual: no forma parte del sitio.
 */
(function () {
  'use strict';

  window.DCLogic = class DCLogic {
    constructor(props) { this.props = props || {}; this.state = {}; }
    setState(patch) { this.state = Object.assign({}, this.state, patch); render(); }
  };

  var fnRegistry = [];
  var template = '';
  var instance = null;
  var mounted = false;
  var hoverSeq = 0;

  function evalExpr(expr, scope) {
    var keys = Object.keys(scope);
    var vals = keys.map(function (k) { return scope[k]; });
    try {
      return new Function(keys.join(','), 'return (' + expr + ');').apply(null, vals);
    } catch (e) {
      console.warn('[dc-shim] expresión no evaluable:', expr, e);
      return '';
    }
  }

  function interpolate(str, scope) {
    return str.replace(/\{\{\s*([\s\S]+?)\s*\}\}/g, function (_, expr) {
      var v = evalExpr(expr, scope);
      if (typeof v === 'function') {
        fnRegistry.push(v);
        return '__dcFn(' + (fnRegistry.length - 1) + ')';
      }
      return v == null ? '' : String(v);
    });
  }

  // Expande <sc-for> respetando anidamiento y luego interpola el resto.
  function expand(str, scope) {
    var out = '';
    var pos = 0;
    var openRe = /<sc-for\b([^>]*)>/g;
    var m;
    while ((m = openRe.exec(str))) {
      out += interpolate(str.slice(pos, m.index), scope);
      var depth = 1;
      var tagRe = /<sc-for\b[^>]*>|<\/sc-for>/g;
      tagRe.lastIndex = openRe.lastIndex;
      var t, bodyEnd = -1, closeEnd = -1;
      while ((t = tagRe.exec(str))) {
        depth += t[0] === '</sc-for>' ? -1 : 1;
        if (depth === 0) { bodyEnd = t.index; closeEnd = tagRe.lastIndex; break; }
      }
      if (bodyEnd < 0) throw new Error('[dc-shim] <sc-for> sin cierre');
      var attrs = m[1];
      var listExpr = (attrs.match(/list="\{\{\s*([\s\S]+?)\s*\}\}"/) || [])[1];
      var asName = (attrs.match(/as="([^"]+)"/) || [])[1] || 'item';
      var body = str.slice(openRe.lastIndex, bodyEnd);
      var list = evalExpr(listExpr, scope) || [];
      list.forEach(function (item, i) {
        var child = Object.assign({}, scope);
        child[asName] = item;
        child.$index = i;
        out += expand(body, child);
      });
      pos = closeEnd;
      openRe.lastIndex = closeEnd;
    }
    out += interpolate(str.slice(pos), scope);
    return out;
  }

  function applyPseudoStyles(root, sheet) {
    [['style-hover', ':hover'], ['style-focus', ':focus']].forEach(function (pair) {
      root.querySelectorAll('[' + pair[0] + ']').forEach(function (el) {
        var cls = 'dcps-' + (++hoverSeq);
        el.classList.add(cls);
        var decls = el.getAttribute(pair[0]).split(';')
          .map(function (d) { return d.trim(); })
          .filter(Boolean)
          .map(function (d) { return d + ' !important'; })
          .join('; ');
        sheet.insertRule('.' + cls + pair[1] + ' { ' + decls + '; }', sheet.cssRules.length);
        el.removeAttribute(pair[0]);
      });
    });
  }

  // Resuelve assets planos ("faena-1.jpg") contra la carpeta assets/.
  function fixAssetPaths(root) {
    root.querySelectorAll('img[src]').forEach(function (img) {
      var src = img.getAttribute('src');
      if (src && !/^(https?:|data:|\/|\.|assets\/)/.test(src)) img.setAttribute('src', 'assets/' + src);
    });
  }

  var host, pseudoSheet;

  function render() {
    // Conservar estados visuales de animaciones ya disparadas entre renders.
    var keep = {};
    ['.reveal', '.hero-in', '.site-header'].forEach(function (sel) {
      keep[sel] = Array.prototype.map.call(document.querySelectorAll(sel), function (el) {
        return el.classList.contains('is-visible');
      });
    });

    fnRegistry = [];
    var vals = instance.renderVals();
    var scope = Object.assign({}, vals);
    host.innerHTML = expand(template, scope);

    pseudoSheet.textContent = '';
    hoverSeq = 0;
    applyPseudoStyles(host, pseudoSheet.sheet);
    fixAssetPaths(host);

    if (mounted) {
      Object.keys(keep).forEach(function (sel) {
        document.querySelectorAll(sel).forEach(function (el, i) {
          if (keep[sel][i]) el.classList.add('is-visible');
        });
      });
      // Re-enganchar observers/listeners sobre los nodos nuevos.
      window.__bkbMotionInit = false;
      if (instance.componentDidMount) instance.componentDidMount();
    }
  }

  window.__dcFn = function (i) { if (fnRegistry[i]) fnRegistry[i](); };

  document.addEventListener('DOMContentLoaded', function () {
    fetch(location.href)
      .then(function (r) { return r.text(); })
      .then(function (raw) {
        var start = raw.indexOf('<x-dc>');
        var end = raw.indexOf('</x-dc>');
        var inner = raw.slice(start + 6, end);

        var helmet = inner.match(/<helmet>([\s\S]*?)<\/helmet>/);
        if (helmet) {
          document.head.insertAdjacentHTML('beforeend', helmet[1]);
          inner = inner.replace(helmet[0], '');
        }
        template = inner;

        var scriptEl = document.querySelector('script[type="text/x-dc"]');
        var propsSpec = JSON.parse(scriptEl.getAttribute('data-props') || '{}');
        var props = {};
        Object.keys(propsSpec).forEach(function (k) { props[k] = propsSpec[k]['default']; });
        var params = new URLSearchParams(location.search);
        params.forEach(function (v, k) { props[k] = v; });

        var Component = new Function('DCLogic', scriptEl.textContent + '\nreturn Component;')(window.DCLogic);
        instance = new Component(props);
        instance.props = props;

        host = document.querySelector('x-dc');
        pseudoSheet = document.createElement('style');
        pseudoSheet.id = 'dc-pseudo-styles';
        document.head.appendChild(pseudoSheet);

        render();
        mounted = true;
        if (instance.componentDidMount) instance.componentDidMount();
      })
      .catch(function (e) { console.error('[dc-shim] error al montar', e); });
  });
})();

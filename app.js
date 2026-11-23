// Open Environments Index: theme toggle, copy buttons, and the home-page filters. No dependencies.
(function () {
  var root = document.documentElement;
  var tbtn = document.getElementById('theme');
  if (tbtn) tbtn.addEventListener('click', function () {
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
  });

  document.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var text = b.parentNode.querySelector('pre').innerText;
      (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(function () {
        b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1400);
      }, function () { b.textContent = 'Select and copy'; });
    });
  });

  var grid = document.getElementById('grid');
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.children);
  var q = document.getElementById('q'), count = document.getElementById('count'), none = document.getElementById('none');
  var more = document.getElementById('more'), clear = document.getElementById('clear'), af = document.getElementById('active-field');
  var sels = Array.prototype.slice.call(document.querySelectorAll('.sel[data-k]'));
  var chks = Array.prototype.slice.call(document.querySelectorAll('.chk input'));
  var sort = document.getElementById('sort');
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tile:not(.empty)'));
  var PAGE = 60, shown = PAGE, field = '';

  var idx = cards.map(function (c) {
    var d = c.dataset;
    return { el: c, d: d, text: d.s, n: { dl: +d.dl, likes: +d.likes, upd: d.upd, tasks: +d.tasks, name: d.name } };
  });

  function apply(keepPage) {
    if (!keepPage) shown = PAGE;
    var terms = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    var hits = idx.filter(function (it) {
      var d = it.d;
      if (field && d.f !== field && d.f2 !== field) return false;
      for (var i = 0; i < sels.length; i++) {
        var v = sels[i].value, k = sels[i].dataset.k;
        if (!v) continue;
        if (k === 'b') { if (d.f.slice(0, 2) !== v) return false; }
        else if ((' ' + d[k] + ' ').indexOf(' ' + v + ' ') < 0) return false;
      }
      for (var j = 0; j < chks.length; j++) if (chks[j].checked && d[chks[j].dataset.k] !== '1') return false;
      for (var t = 0; t < terms.length; t++) if (it.text.indexOf(terms[t]) < 0) return false;
      return true;
    });
    var s = sort.value;
    hits.sort(function (a, b) {
      if (s === 'name') return a.n.name.localeCompare(b.n.name);
      if (s === 'upd') return b.n.upd.localeCompare(a.n.upd);
      return (b.n[s] - a.n[s]) || (b.n.dl - a.n.dl);
    });
    idx.forEach(function (it) { it.el.hidden = true; });
    hits.forEach(function (it, i) { it.el.hidden = i >= shown; grid.appendChild(it.el); });
    count.textContent = hits.length + (hits.length === 1 ? ' environment' : ' environments');
    none.hidden = hits.length > 0;
    more.hidden = hits.length <= shown;
    more.textContent = 'Show ' + Math.min(PAGE, hits.length - shown) + ' more';
    sels.forEach(function (x) { x.classList.toggle('on', !!x.value); });
    var any = field || q.value || sels.some(function (x) { return x.value; }) || chks.some(function (x) { return x.checked; });
    clear.hidden = !any;
    tiles.forEach(function (t) { t.setAttribute('aria-pressed', t.dataset.code === field ? 'true' : 'false'); });
    if (field) {
      var t = document.querySelector('.tile[data-code="' + field + '"]');
      af.innerHTML = 'Field <b>' + field + ' ' + (t ? t.dataset.name : '') + '</b> · <button class="clear" id="unfield">show all fields</button>';
      af.hidden = false;
      document.getElementById('unfield').onclick = function () { field = ''; apply(); };
    } else af.hidden = true;
    var p = new URLSearchParams();
    if (field) p.set('field', field);
    if (q.value) p.set('q', q.value);
    sels.forEach(function (x) { if (x.value) p.set(x.dataset.k, x.value); });
    chks.forEach(function (x) { if (x.checked) p.set(x.dataset.k, '1'); });
    if (sort.value !== 'dl') p.set('sort', sort.value);
    var h = p.toString();
    history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
  }

  tiles.forEach(function (t) {
    t.addEventListener('click', function () {
      field = field === t.dataset.code ? '' : t.dataset.code;
      sels.forEach(function (x) { if (x.dataset.k === 'b') x.value = ''; });
      apply();
      document.getElementById('directory').scrollIntoView({ block: 'start' });
    });
  });
  q.addEventListener('input', function () { apply(); });
  sels.concat(chks, [sort]).forEach(function (x) { x.addEventListener('change', function () { apply(); }); });
  more.addEventListener('click', function () { shown += PAGE; apply(true); });
  clear.addEventListener('click', function () {
    field = ''; q.value = ''; sels.forEach(function (x) { x.value = ''; }); chks.forEach(function (x) { x.checked = false; }); apply();
  });

  var p = new URLSearchParams(location.hash.slice(1));
  field = p.get('field') || '';
  q.value = p.get('q') || '';
  sels.forEach(function (x) { if (p.get(x.dataset.k)) x.value = p.get(x.dataset.k); });
  chks.forEach(function (x) { x.checked = p.get(x.dataset.k) === '1'; });
  if (p.get('sort')) sort.value = p.get('sort');
  apply();
  if (location.hash.length > 1) document.getElementById('directory').scrollIntoView({ block: 'start' });
  window.addEventListener('hashchange', function () { location.reload(); });
})();

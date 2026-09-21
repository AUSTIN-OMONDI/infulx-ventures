/* Infulx Ventures storefront script */
(function () {
  "use strict";
  var KEY = "infulx_cart";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var money = function (n) { return "KSh " + Math.round(n).toLocaleString("en-KE"); };
  var esc = function (s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; };

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save(c) {
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
    updateCount();
  }
  function updateCount() {
    var c = load(), n = 0;
    Object.keys(c).forEach(function (k) { n += c[k]; });
    $$("[data-cart-count]").forEach(function (el) { el.textContent = n; el.classList.toggle("has", n > 0); });
  }

  var toastTimer;
  function toast(msg) {
    var t = $("#toast");
    if (!t) return;
    t.innerHTML = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }

  var Cart = {
    add: function (id, qty) {
      var c = load();
      c[id] = Math.min((c[id] || 0) + (qty || 1), 10000);
      save(c);
    },
    set: function (id, qty) {
      var c = load();
      if (qty > 0) c[id] = Math.min(qty, 10000); else delete c[id];
      save(c);
    },
    clear: function () { save({}); },

    renderPage: function () {
      var c = load(), ids = Object.keys(c);
      var loading = $("#cartLoading");
      if (!ids.length) { loading.hidden = true; $("#cartEmpty").hidden = false; $("#cartWrap").hidden = true; return; }
      fetch("/api/products?ids=" + ids.join(","))
        .then(function (r) { return r.json(); })
        .then(function (products) {
          loading.hidden = true;
          // drop items that no longer exist
          var known = {};
          products.forEach(function (p) { known[p.id] = p; });
          ids.forEach(function (id) { if (!known[id]) delete c[id]; });
          save(c);
          Cart._draw(products);
        })
        .catch(function () { loading.textContent = "Could not load your cart. Please refresh the page."; });
    },

    _draw: function (products) {
      var c = load();
      var list = products.filter(function (p) { return c[p.id]; });
      if (!list.length) { $("#cartEmpty").hidden = false; $("#cartWrap").hidden = true; return; }
      $("#cartEmpty").hidden = true; $("#cartWrap").hidden = false;
      var total = 0, count = 0, html = "", hidden = "";
      list.forEach(function (p) {
        var q = c[p.id], line = q * p.price;
        if (p.in_stock) { total += line; count += q; hidden += '<input type="hidden" name="qty_' + p.id + '" value="' + q + '">'; }
        html += '<div class="ci' + (p.in_stock ? "" : " ci-out") + '">' +
          '<a href="' + p.url + '" class="ci-img"><img src="' + p.image + '" alt=""></a>' +
          '<div class="ci-info"><a href="' + p.url + '" class="ci-name">' + esc(p.name) + '</a>' +
          '<span class="muted">' + money(p.price) + ' each</span>' +
          (p.in_stock ? "" : '<span class="stock out">Out of stock – will not be ordered</span>') +
          '<div class="ci-row"><div class="qty qty-sm">' +
          '<button type="button" data-cq="' + p.id + '" data-d="-1" aria-label="Decrease">−</button>' +
          '<input type="number" min="1" value="' + q + '" data-cqi="' + p.id + '" aria-label="Quantity">' +
          '<button type="button" data-cq="' + p.id + '" data-d="1" aria-label="Increase">+</button></div>' +
          '<b class="ci-line">' + money(line) + '</b></div>' +
          '<button type="button" class="ci-rm" data-rm="' + p.id + '">Remove</button></div></div>';
      });
      $("#cartItems").innerHTML = html;
      $("#cartHidden").innerHTML = hidden;
      $("#sumCount").textContent = count;
      $("#sumTotal").textContent = money(total);

      var redraw = function () { Cart._draw(products); };
      $$("[data-cq]").forEach(function (b) {
        b.onclick = function () { var id = b.dataset.cq; Cart.set(id, (load()[id] || 0) + (+b.dataset.d)); redraw(); };
      });
      $$("[data-cqi]").forEach(function (i) {
        i.onchange = function () { Cart.set(i.dataset.cqi, Math.max(1, parseInt(i.value, 10) || 1)); redraw(); };
      });
      $$("[data-rm]").forEach(function (b) {
        b.onclick = function () { Cart.set(b.dataset.rm, 0); redraw(); };
      });
    }
  };
  window.Cart = Cart;

  document.addEventListener("click", function (e) {
    var add = e.target.closest("[data-add]");
    if (add) {
      var qtyEl = add.dataset.qtyFrom ? $(add.dataset.qtyFrom) : null;
      var qty = qtyEl ? Math.max(1, parseInt(qtyEl.value, 10) || 1) : 1;
      Cart.add(add.dataset.add, qty);
      toast("✓ Added <b>" + esc(add.dataset.name || "item") + "</b> to cart · <a href='/cart'>View cart</a>");
      return;
    }
    var buy = e.target.closest("[data-buy-now]");
    if (buy) {
      var qi = $("#qty");
      var c = load();
      if (!c[buy.dataset.buyNow]) Cart.add(buy.dataset.buyNow, qi ? Math.max(1, parseInt(qi.value, 10) || 1) : 1);
      return; // link continues to /cart
    }
    var step = e.target.closest("[data-step]");
    if (step) {
      var input = step.parentNode.querySelector("input");
      input.value = Math.max(1, (parseInt(input.value, 10) || 1) + (+step.dataset.step));
      return;
    }
    var copy = e.target.closest("[data-copy]");
    if (copy) {
      var text = copy.dataset.copy;
      var done = function () { copy.textContent = "Copied!"; setTimeout(function () { copy.textContent = "Copy"; }, 1500); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, done);
      else {
        var ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch (err) {}
        document.body.removeChild(ta); done();
      }
      return;
    }
    if (e.target.closest("[data-open-pay]")) { $("#payModal").hidden = false; return; }
    if (e.target.closest("[data-close-pay]") || e.target.id === "payModal") { $("#payModal").hidden = true; return; }
    var th = e.target.closest("[data-thumb]");
    if (th) {
      $("#mainImg").src = th.dataset.thumb;
      $$("[data-thumb]").forEach(function (b) { b.classList.toggle("on", b === th); });
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && $("#payModal")) $("#payModal").hidden = true;
  });

  updateCount();
})();

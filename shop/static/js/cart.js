/* AURELIA cart drawer: renders from /cart/data/ and talks to the cart endpoints */
(() => {
  'use strict';
  const { $, post, toast, openPanel } = window.Aurelia;
  const drawer = $('#cart-drawer');
  if (!drawer) return;
  const body = $('#cart-body', drawer);
  const foot = $('#cart-foot', drawer);
  const urls = drawer.dataset;
  const badges = Array.from(document.querySelectorAll('[data-cart-count]'));

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setBadge(count) {
    badges.forEach(b => { b.textContent = count; b.dataset.zero = String(count === 0); b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump'); });
  }

  function render(cart) {
    setBadge(cart.count);
    body.replaceChildren();
    if (!cart.items.length) {
      const empty = el('div', 'empty-state');
      empty.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-bag"/></svg>';
      empty.append(el('h3', '', 'Your cart is empty'), el('p', '', 'Discover pieces made to be kept.'));
      const link = el('a', 'btn btn-outline', 'Continue shopping');
      link.href = urls.shopUrl;
      empty.append(link);
      body.append(empty);
      foot.hidden = true;
      return;
    }
    foot.hidden = false;

    const ship = el('div', 'free-ship');
    if (cart.to_free_shipping) {
      ship.append('Add ', Object.assign(el('strong', '', cart.to_free_shipping)), ' more for complimentary shipping.');
    } else {
      ship.append(Object.assign(el('strong', '', 'You qualify for complimentary shipping.')));
    }
    const bar = el('div', 'free-ship-bar'); const fill = el('span'); fill.style.width = cart.free_shipping_progress + '%'; bar.append(fill); ship.append(bar);
    body.append(ship);

    cart.items.forEach(item => {
      const line = el('div', 'cart-line');
      const img = el('img'); img.src = item.image; img.alt = item.name; img.width = 78; img.height = 78; img.loading = 'lazy';
      const imgLink = el('a'); imgLink.href = item.url; imgLink.append(img);
      const info = el('div');
      const title = el('h3'); const a = el('a', '', item.name); a.href = item.url; title.append(a);
      const meta = [item.brand, item.size && 'Size ' + item.size, item.color].filter(Boolean).join(' · ');
      const row = el('div', 'row');
      const qty = el('div', 'qty sm');
      const minus = el('button', '', ''); minus.type = 'button'; minus.setAttribute('aria-label', 'Decrease quantity');
      minus.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-minus"/></svg>';
      minus.dataset.cartKey = item.key; minus.dataset.cartQty = String(item.quantity - 1);
      const num = el('input'); num.value = item.quantity; num.readOnly = true; num.setAttribute('aria-label', 'Quantity'); num.tabIndex = -1;
      const plus = el('button', '', ''); plus.type = 'button'; plus.setAttribute('aria-label', 'Increase quantity');
      plus.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg>';
      plus.dataset.cartKey = item.key; plus.dataset.cartQty = String(item.quantity + 1); plus.disabled = item.quantity >= item.max;
      qty.append(minus, num, plus);
      row.append(qty, el('span', 'price', item.line_total));
      const remove = el('button', 'line-remove', 'Remove'); remove.type = 'button'; remove.dataset.cartKey = item.key; remove.dataset.cartRemove = '1';
      info.append(title, el('p', 'meta', meta), row, remove);
      line.append(imgLink, info);
      body.append(line);
    });

    $('[data-cart-subtotal]', foot).textContent = cart.subtotal;
    $('[data-cart-shipping]', foot).textContent = cart.shipping;
    $('[data-cart-total]', foot).textContent = cart.total;
  }

  async function load() {
    body.setAttribute('aria-busy', 'true');
    try {
      const res = await fetch(urls.dataUrl, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
      const data = await res.json();
      render(data.cart);
    } catch (_) {
      body.replaceChildren(el('p', 'text-muted', 'We could not load your cart. Please refresh the page.'));
    } finally { body.removeAttribute('aria-busy'); }
  }

  drawer.addEventListener('panel:open', load);

  // Add to cart (product page + quick-add buttons). "Buy now" falls through to a normal submit.
  document.addEventListener('submit', async e => {
    const form = e.target.closest('[data-add-to-cart]');
    if (!form) return;
    if (e.submitter && e.submitter.name === 'buy_now') return;
    e.preventDefault();
    const btn = e.submitter || $('button[type="submit"]', form);
    btn.classList.add('is-loading');
    const { ok, data } = await post(form.action, new FormData(form));
    btn.classList.remove('is-loading');
    if (!ok) { toast(data.message, 'error'); return; }
    render(data.cart);
    openPanel(drawer);
  });

  async function mutate(url, payload) {
    const fd = new FormData();
    Object.entries(payload).forEach(([k, v]) => fd.append(k, v));
    const { ok, data } = await post(url, fd);
    if (data.cart) render(data.cart);
    if (!ok) toast(data.message, 'error');
  }

  drawer.addEventListener('click', e => {
    const qtyBtn = e.target.closest('[data-cart-qty]');
    if (qtyBtn && !qtyBtn.disabled) { mutate(urls.updateUrl, { key: qtyBtn.dataset.cartKey, quantity: qtyBtn.dataset.cartQty }); return; }
    const rm = e.target.closest('[data-cart-remove]');
    if (rm) mutate(urls.removeUrl, { key: rm.dataset.cartKey });
  });
})();

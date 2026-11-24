/* AURELIA core: helpers, toasts, header, drawers, page transitions, wishlist, newsletter */
(() => {
  'use strict';
  document.documentElement.classList.add('js');

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---- network helper ------------------------------------------------------- */
  const csrfToken = () => {
    const meta = $('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  };

  async function post(url, body) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        body,
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json' },
      });
      let data = {};
      try { data = await res.json(); } catch (_) { /* non-JSON error page */ }
      if (!res.ok && !data.message) data.message = 'Something went wrong. Please try again.';
      return { ok: res.ok && data.ok !== false, data };
    } catch (err) {
      return { ok: false, data: { message: 'Network error — please check your connection and try again.' } };
    }
  }

  /* ---- toasts ----------------------------------------------------------------- */
  const toastHost = $('#toasts');
  function toast(message, type = 'success') {
    if (!toastHost || !message) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');
    el.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-' + (type === 'error' ? 'close' : 'check') + '"/></svg><p></p>' +
      '<button type="button" aria-label="Dismiss"><svg class="icon" aria-hidden="true"><use href="#i-close"/></svg></button>';
    $('p', el).textContent = message;
    const remove = () => { el.classList.add('leaving'); setTimeout(() => el.remove(), 280); };
    $('button', el).addEventListener('click', remove);
    toastHost.appendChild(el);
    while (toastHost.children.length > 3) toastHost.firstElementChild.remove();
    setTimeout(remove, type === 'error' ? 6500 : 4200);
  }

  $$('#flash li').forEach((li, i) => setTimeout(() => toast(li.textContent.trim(), li.dataset.level === 'error' ? 'error' : 'success'), 350 + i * 250));

  /* ---- overlay + drawers ------------------------------------------------------ */
  const overlay = $('#overlay');
  let lastFocus = null;
  function openPanel(el) {
    if (!el) return;
    closePanels(true);
    lastFocus = document.activeElement;
    el.classList.add('is-open');
    el.setAttribute('aria-hidden', 'false');
    overlay.classList.add('is-open');
    document.body.classList.add('no-scroll');
    const focusable = $('button, a[href], input, select', el);
    setTimeout(() => focusable && focusable.focus({ preventScroll: true }), 120);
    el.dispatchEvent(new CustomEvent('panel:open'));
  }
  function closePanels(silent) {
    $$('.drawer.is-open, .filters.is-open').forEach(p => { p.classList.remove('is-open'); p.setAttribute('aria-hidden', 'true'); });
    overlay.classList.remove('is-open');
    document.body.classList.remove('no-scroll');
    $$('[data-nav-toggle]').forEach(b => b.setAttribute('aria-expanded', 'false'));
    if (!silent && lastFocus) { lastFocus.focus({ preventScroll: true }); lastFocus = null; }
  }
  document.addEventListener('click', e => {
    const opener = e.target.closest('[data-open-panel]');
    if (opener) {
      e.preventDefault();
      openPanel(document.getElementById(opener.dataset.openPanel));
      if (opener.hasAttribute('data-nav-toggle')) opener.setAttribute('aria-expanded', 'true');
    } else if (e.target.closest('[data-close-panel]') || e.target === overlay) {
      closePanels();
    }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closePanels(); closeSearch(); }
    if (e.key === 'Tab') {
      const open = $('.drawer.is-open, .filters.is-open');
      if (!open) return;
      const items = $$('button:not([disabled]), a[href], input:not([type=hidden]), select, textarea', open).filter(x => x.offsetParent !== null);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  /* ---- search bar + header ---------------------------------------------------- */
  const searchBar = $('#search-bar');
  function closeSearch() { if (searchBar) searchBar.classList.remove('is-open'); }
  $$('[data-search-toggle]').forEach(btn => btn.addEventListener('click', () => {
    if (!searchBar) return;
    const open = searchBar.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', String(open));
    if (open) setTimeout(() => $('input', searchBar).focus(), 150);
  }));

  const header = $('.site-header');
  const onScroll = () => header && header.classList.toggle('is-scrolled', window.scrollY > 10);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- page transitions + reveal --------------------------------------------- */
  requestAnimationFrame(() => document.body.classList.add('is-loaded'));
  window.addEventListener('pageshow', e => { if (e.persisted) document.body.classList.remove('is-leaving'); });
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (a.target && a.target !== '_self') return;
    if (a.hasAttribute('download') || a.origin !== location.origin) return;
    if (a.pathname === location.pathname && a.search === location.search) return; // same page / hash jumps
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    e.preventDefault();
    document.body.classList.add('is-leaving');
    setTimeout(() => { location.href = a.href; }, 170);
  });

  const revealables = $$('[data-reveal]');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    revealables.forEach((el, i) => { el.style.transitionDelay = `${Math.min(i % 4, 3) * 70}ms`; io.observe(el); });
  } else {
    revealables.forEach(el => el.classList.add('is-visible'));
  }

  /* ---- quantity steppers ------------------------------------------------------ */
  document.addEventListener('click', e => {
    const btn = e.target.closest('.qty [data-step]');
    if (!btn) return;
    const input = $('input', btn.closest('.qty'));
    const min = parseInt(input.min || '1', 10), max = parseInt(input.max || '99', 10);
    const next = Math.min(max, Math.max(min, (parseInt(input.value, 10) || min) + parseInt(btn.dataset.step, 10)));
    if (next !== parseInt(input.value, 10)) { input.value = next; input.dispatchEvent(new Event('change', { bubbles: true })); }
    syncStepper(btn.closest('.qty'));
  });
  function syncStepper(qty) {
    const input = $('input', qty);
    const min = parseInt(input.min || '1', 10), max = parseInt(input.max || '99', 10);
    const v = parseInt(input.value, 10) || min;
    $$('[data-step]', qty).forEach(b => { b.disabled = (parseInt(b.dataset.step, 10) < 0 && v <= min) || (parseInt(b.dataset.step, 10) > 0 && v >= max); });
  }
  $$('.qty').forEach(syncStepper);
  document.addEventListener('change', e => {
    if (e.target.matches('.qty input')) {
      const input = e.target;
      const min = parseInt(input.min || '1', 10), max = parseInt(input.max || '99', 10);
      input.value = Math.min(max, Math.max(min, parseInt(input.value, 10) || min));
      syncStepper(input.closest('.qty'));
    }
    const form = e.target.closest('form[data-autosubmit]');
    if (form && e.target.matches('.qty input')) form.requestSubmit();
  });

  /* ---- loading state for ordinary form submits -------------------------------- */
  document.addEventListener('submit', e => {
    const form = e.target;
    if (e.defaultPrevented || form.hasAttribute('data-no-loading') || form.matches('[data-add-to-cart], [data-wishlist-form], [data-newsletter]')) return;
    const submitter = e.submitter || $('button[type="submit"]', form);
    if (submitter && submitter.classList.contains('btn')) submitter.classList.add('is-loading');
  });
  window.addEventListener('pageshow', () => $$('.btn.is-loading').forEach(b => b.classList.remove('is-loading')));

  /* ---- wishlist --------------------------------------------------------------- */
  const wishCount = $$('[data-wishlist-count]');
  function setWishCount(n) {
    wishCount.forEach(el => { el.textContent = n; el.dataset.zero = String(n === 0); el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); });
  }
  document.addEventListener('submit', async e => {
    const form = e.target.closest('[data-wishlist-form]');
    if (!form) return;
    e.preventDefault();
    const id = form.dataset.productId;
    const { ok, data } = await post(form.action, new FormData(form));
    if (!ok) { toast(data.message, 'error'); return; }
    $$(`[data-wishlist-form][data-product-id="${id}"] button[data-wish]`).forEach(btn => {
      btn.classList.toggle('is-active', data.added);
      btn.setAttribute('aria-pressed', String(data.added));
      const label = $('[data-wish-label]', btn);
      if (label) label.textContent = data.added ? 'Saved to wishlist' : 'Add to wishlist';
      btn.classList.remove('pop'); void btn.offsetWidth; btn.classList.add('pop');
    });
    setWishCount(data.count);
    toast(data.message);
    const page = $('[data-wishlist-page]');
    if (page && !data.added) {
      const card = form.closest('.product-card');
      if (card) {
        card.style.transition = 'opacity .3s, transform .3s'; card.style.opacity = '0'; card.style.transform = 'scale(.96)';
        setTimeout(() => {
          card.remove();
          if (!$('.product-card', page)) location.reload();
        }, 300);
      }
    }
  });

  /* ---- newsletter ------------------------------------------------------------- */
  document.addEventListener('submit', async e => {
    const form = e.target.closest('[data-newsletter]');
    if (!form) return;
    e.preventDefault();
    const btn = $('button[type="submit"]', form);
    btn.classList.add('is-loading');
    const { ok, data } = await post(form.action, new FormData(form));
    btn.classList.remove('is-loading');
    toast(data.message, ok ? 'success' : 'error');
    if (ok) form.reset();
  });

  window.Aurelia = { $, $$, post, toast, openPanel, closePanels };
})();

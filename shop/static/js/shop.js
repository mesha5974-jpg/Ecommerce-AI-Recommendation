/* Shop page: filter drawer (mobile), auto-applied filters with a loading state */
(() => {
  'use strict';
  const form = document.getElementById('filter-form');
  const grid = document.getElementById('product-grid');
  if (!form) return;

  let timer;
  function apply() {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (grid) grid.classList.add('is-loading-grid');
      const page = form.querySelector('input[name="page"]');
      if (page) page.remove();
      form.requestSubmit();
    }, 250);
  }

  const watched = el => el.matches('input[type="checkbox"], input[type="radio"], select, input[type="number"]');
  document.addEventListener('change', e => {
    if (!watched(e.target)) return;
    if (e.target.form === form || e.target.getAttribute('form') === form.id) apply();
  });

  form.addEventListener('submit', () => {
    // Drop empty parameters so shareable URLs stay clean.
    Array.from(form.elements).forEach(el => {
      if (el.name && el.type !== 'submit' && el.value === '' && el.type !== 'checkbox' && el.type !== 'radio') el.disabled = true;
    });
    if (grid) grid.classList.add('is-loading-grid');
  });
  window.addEventListener('pageshow', () => {
    Array.from(form.elements).forEach(el => { el.disabled = false; });
    if (grid) grid.classList.remove('is-loading-grid');
  });

  document.querySelectorAll('.chip, .chip-clear, .pagination a').forEach(a => a.addEventListener('click', () => grid && grid.classList.add('is-loading-grid')));
})();

/* Product page: gallery + hover zoom, option labels, review star input */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // Gallery
  const main = $('#gallery-main');
  const mainImg = main && $('img', main);
  $$('[data-thumb]').forEach(btn => btn.addEventListener('click', () => {
    if (!mainImg) return;
    mainImg.style.opacity = '0';
    setTimeout(() => {
      mainImg.src = btn.dataset.src;
      mainImg.alt = btn.dataset.alt;
      mainImg.style.opacity = '1';
    }, 140);
    $$('[data-thumb]').forEach(b => b.removeAttribute('aria-current'));
    btn.setAttribute('aria-current', 'true');
  }));
  if (main && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    main.addEventListener('mouseenter', () => main.classList.add('is-zoomed'));
    main.addEventListener('mouseleave', () => main.classList.remove('is-zoomed'));
    main.addEventListener('mousemove', e => {
      const r = main.getBoundingClientRect();
      main.style.setProperty('--zx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%');
      main.style.setProperty('--zy', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%');
    });
  }

  // Show the selected size / colour next to the legend
  $$('.option-group').forEach(group => {
    const out = $('[data-selected]', group);
    group.addEventListener('change', e => { if (out && e.target.matches('input')) out.textContent = e.target.value; });
  });

  // Review stars
  const stars = $$('[data-star]');
  const ratingInput = $('#id_rating');
  stars.forEach(btn => btn.addEventListener('click', () => {
    const value = parseInt(btn.dataset.star, 10);
    ratingInput.value = value;
    stars.forEach(s => {
      const on = parseInt(s.dataset.star, 10) <= value;
      s.classList.toggle('on', on);
      s.setAttribute('aria-pressed', String(on));
    });
  }));
  const reviewForm = $('#review-form');
  if (reviewForm) reviewForm.addEventListener('submit', e => {
    if (!ratingInput.value) {
      e.preventDefault();
      window.Aurelia && window.Aurelia.toast('Please choose a star rating first.', 'error');
    }
  });
})();

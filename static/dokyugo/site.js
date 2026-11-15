'use strict';
const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('#site-nav');
if (menuButton && nav) {
  const closeMenu = () => { nav.classList.remove('is-open'); menuButton.setAttribute('aria-expanded', 'false'); };
  menuButton.addEventListener('click', () => {
    const expanded = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!expanded));
    nav.classList.toggle('is-open', !expanded);
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('is-open')) { closeMenu(); menuButton.focus(); } });
  document.addEventListener('click', event => { if (!event.target.closest('.site-header')) closeMenu(); });
  window.matchMedia('(min-width:701px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
}

const noMiddleName = document.querySelector('#id_no_middle_name');
const middleName = document.querySelector('#id_middle_name');
if (noMiddleName && middleName) {
  const sync = () => { middleName.disabled = noMiddleName.checked; middleName.required = !noMiddleName.checked; };
  noMiddleName.addEventListener('change', sync); sync();
}

document.querySelectorAll('[data-checklist]').forEach(list => {
  const key = `dokyugo-checklist:${list.dataset.checklist}`;
  let saved = {};
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || '{}');
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) saved = parsed;
  } catch (_) { /* Storage can be disabled. */ }
  list.querySelectorAll('input[data-item]').forEach(input => {
    input.checked = Boolean(saved[input.dataset.item]);
    input.addEventListener('change', () => {
      saved[input.dataset.item] = input.checked;
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch (_) { /* Checklist still works in memory. */ }
    });
  });
});

document.querySelectorAll('[data-print-ticket]').forEach(button => button.addEventListener('click', () => window.print()));

const liveTicket = document.querySelector('[data-live-ticket]');
if (liveTicket) {
  let timer;
  const poll = async () => {
    if (document.hidden) return;
    try {
      const response = await fetch(liveTicket.dataset.liveTicket, {credentials: 'same-origin', headers: {'Accept': 'application/json'}});
      if (!response.ok) return;
      const booking = await response.json();
      const status = document.querySelector('[data-ticket-status]');
      if (status) { status.textContent = booking.status_label; status.className = `status status-${booking.status}`; }
      if (!booking.can_change) document.querySelectorAll('[data-change-booking]').forEach(action => action.hidden = true);
      if (['completed', 'cancelled', 'missed'].includes(booking.status)) clearInterval(timer);
    } catch (_) { /* Keep the last known state when offline. */ }
  };
  timer = setInterval(poll, 15000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
}

document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!form.checkValidity()) return;
    // Named submit buttons carry the staff action and must remain in the POST.
    if (event.submitter && event.submitter.name) return;
    const submit = event.submitter || form.querySelector('button[type="submit"], button:not([type])');
    queueMicrotask(() => {
      if (!event.defaultPrevented && submit) { submit.disabled = true; submit.setAttribute('aria-busy', 'true'); }
    });
  });
});
window.addEventListener('pageshow', () => document.querySelectorAll('button[aria-busy="true"]').forEach(button => { button.disabled = false; button.removeAttribute('aria-busy'); }));

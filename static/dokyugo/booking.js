'use strict';
(() => {
  const root = document.querySelector('[data-appointment-picker]');
  const configNode = document.getElementById('appointment-config');
  const select = document.getElementById('id_slot');
  if (!root || !configNode || !select) return;
  const config = JSON.parse(configNode.textContent);
  const fallback = document.querySelector('[data-slot-fallback]');
  const monthLabel = root.querySelector('[data-month-label]');
  const grid = root.querySelector('[data-calendar-grid]');
  const status = root.querySelector('[data-calendar-status]');
  const times = root.querySelector('[data-time-slots]');
  const previous = root.querySelector('[data-month-prev]');
  const next = root.querySelector('[data-month-next]');
  const longDate = new Intl.DateTimeFormat('en-PH', {weekday:'long', month:'long', day:'numeric', year:'numeric', timeZone:'Asia/Manila'});
  const shortDate = new Intl.DateTimeFormat('en-PH', {month:'short', day:'numeric', year:'numeric', timeZone:'Asia/Manila'});
  const parseDay = key => new Date(`${key}T12:00:00+08:00`);
  const inManila = {timeZone:'Asia/Manila'};
  let month = config.month, selectedDate = config.selectedDate, days = new Map(), slots = new Map(), controller;
  let serial = 0;
  root.hidden = false;

  function notify(slot) {
    // Availability can change after the form was rendered (for example, an admin
    // publishes a new time). Keep the fallback field in sync with live choices.
    if (slot && ![...select.options].some(option=>option.value===String(slot.id))) {
      select.add(new Option(`${shortDate.format(new Date(slot.starts_at))} · ${slot.time}`,String(slot.id)));
    }
    select.value = slot ? String(slot.id) : '';
    select.dispatchEvent(new Event('change', {bubbles:true}));
    document.dispatchEvent(new CustomEvent('appointment:change', {detail: slot ? {slot, dateLabel:shortDate.format(new Date(slot.starts_at))} : null}));
  }
  function renderDays() {
    const [year, number] = month.split('-').map(Number);
    const first = new Date(year, number-1, 1);
    monthLabel.textContent = new Intl.DateTimeFormat('en-PH', {month:'long', year:'numeric'}).format(first);
    previous.disabled = month <= config.minMonth;
    next.disabled = month >= config.maxMonth;
    grid.replaceChildren();
    for (let i=0; i<first.getDay(); i++) {
      const blank = document.createElement('span'); blank.setAttribute('aria-hidden','true'); grid.append(blank);
    }
    const length = new Date(year, number, 0).getDate();
    for (let day=1; day<=length; day++) {
      const key = `${month}-${String(day).padStart(2,'0')}`;
      const info = days.get(key);
      const available = key >= config.today && Boolean(info && info.remaining > 0);
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'calendar-day'; button.dataset.date = key;
      button.disabled = !available;
      button.setAttribute('aria-pressed', String(selectedDate === key && available));
      button.setAttribute('aria-label', `${longDate.format(parseDay(key))}, ${available ? info.remaining+' places available' : 'unavailable'}`);
      if (key === config.today) button.setAttribute('aria-current','date');
      const numberText = document.createElement('span'); numberText.textContent = String(day); button.append(numberText);
      if (available) { const dot = document.createElement('i'); dot.setAttribute('aria-hidden','true'); button.append(dot); }
      button.addEventListener('click', () => {
        selectedDate = key; notify(null); renderDays(); renderTimes();
        grid.querySelector(`[data-date="${key}"]`)?.focus();
      });
      button.addEventListener('keydown', event => {
        const moves = {ArrowLeft:-1, ArrowRight:1, ArrowUp:-7, ArrowDown:7};
        if (!(event.key in moves)) return;
        event.preventDefault();
        const buttons = [...grid.querySelectorAll('button')];
        let index = buttons.indexOf(button) + moves[event.key];
        while (index >= 0 && index < buttons.length) {
          if (!buttons[index].disabled) { buttons[index].focus(); break; }
          index += Math.sign(moves[event.key]);
        }
      });
      grid.append(button);
    }
  }
  function renderTimes() {
    times.replaceChildren();
    const day = days.get(selectedDate);
    root.querySelector('[data-time-date]').textContent = day ? longDate.format(parseDay(selectedDate)) : 'Select an available day';
    if (!day || !day.slots.length) {
      const empty = document.createElement('p'); empty.className='time-empty'; empty.textContent='Choose a highlighted date to see its appointment times.'; times.append(empty); return;
    }
    let period = '';
    for (const slot of day.slots) {
      const localHour = Number(new Intl.DateTimeFormat('en-GB', {hour:'2-digit', hourCycle:'h23', ...inManila}).format(new Date(slot.starts_at)));
      const label = localHour < 12 ? 'Morning' : 'Afternoon';
      if (label !== period) { const heading=document.createElement('h4'); heading.textContent=label; times.append(heading); period=label; }
      const button=document.createElement('button'); button.type='button'; button.className='time-slot'; button.dataset.slot=String(slot.id);
      button.disabled=!slot.available; button.setAttribute('aria-pressed', String(select.value===String(slot.id)));
      const strong=document.createElement('strong'); strong.textContent=slot.time;
      const small=document.createElement('small'); small.textContent=slot.available ? `${slot.remaining} ${slot.remaining===1?'place':'places'} left` : slot.reason;
      button.append(strong,small);
      button.addEventListener('click', () => loadMonth(String(slot.id)));
      times.append(button);
    }
  }
  async function loadMonth(preferred=select.value) {
    if (controller) controller.abort();
    controller=new AbortController(); const run=++serial;
    root.setAttribute('aria-busy','true'); status.textContent='Checking available appointments…';
    const url=new URL(config.endpoint, location.origin); url.searchParams.set('month',month);
    const selectedDocuments=[...document.querySelectorAll('input[name="documents"]:checked')].map(input=>input.value);
    if (selectedDocuments.length) url.searchParams.set('documents',selectedDocuments.join(','));
    try {
      const response=await fetch(url, {credentials:'same-origin',signal:controller.signal,headers:{Accept:'application/json'}});
      const data=await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not load appointments.');
      if (run !== serial) return;
      days=new Map(data.days.map(day=>[day.date,day]));
      slots=new Map(data.days.flatMap(day=>day.slots).map(slot=>[String(slot.id),slot]));
      const chosen=slots.get(String(preferred));
      if (chosen?.available) selectedDate=chosen.starts_at.slice(0,10);
      else if (!days.get(selectedDate)?.remaining) selectedDate=data.days.find(day=>day.remaining>0)?.date || '';
      notify(chosen?.available ? chosen : null);
      renderDays(); renderTimes(); fallback.hidden=true;
      const total=data.days.reduce((sum,day)=>sum+day.remaining,0);
      status.textContent=total ? 'Select a highlighted date, then choose an available time.' : 'No open appointments this month. Try the next month or check again later.';
      if (preferred && !chosen?.available) status.textContent='That time is no longer available. Please choose another appointment.';
    } catch (error) {
      if (error.name==='AbortError') return;
      status.textContent=`${error.message} You can use the appointment list below or retry.`;
      fallback.hidden=false;
    } finally { if (run===serial) root.removeAttribute('aria-busy'); }
  }
  function changeMonth(offset) {
    const [year,number]=month.split('-').map(Number);
    const target=new Date(year,number-1+offset,1);
    month=`${target.getFullYear()}-${String(target.getMonth()+1).padStart(2,'0')}`;
    selectedDate=''; notify(null); loadMonth('');
  }
  previous.addEventListener('click',()=>changeMonth(-1)); next.addEventListener('click',()=>changeMonth(1));
  root.querySelector('[data-refresh-calendar]').addEventListener('click',()=>loadMonth());

  const form=document.querySelector('[data-booking-form]');
  if (form) {
    const review=form.querySelector('[data-review-booking]');
    const confirm=form.querySelector('[data-confirm-booking]');
    const panel=form.querySelector('[data-review-panel]');
    const error=form.querySelector('[data-booking-error]');
    const docInputs=[...form.querySelectorAll('input[name="documents"]')];
    let reviewed=false;
    function resetReview() { reviewed=false; review.hidden=false; confirm.hidden=true; panel.hidden=true; error.textContent=''; }
    function updateDocuments() {
      const list=form.querySelector('[data-summary-documents]'); list.replaceChildren();
      const checked=docInputs.filter(input=>input.checked);
      for (const input of checked) { const li=document.createElement('li'); li.textContent=input.closest('label').textContent.trim(); list.append(li); }
      if (!checked.length) { const li=document.createElement('li'); li.textContent='Choose a document to get started.'; list.append(li); }
      resetReview();
    }
    function validate() {
      let message='';
      if (!docInputs.some(input=>input.checked)) message='Choose at least one document.';
      else if (!select.value) message='Choose an available appointment date and time.';
      else if (!form.querySelector('#id_prepared').checked) message='Confirm that you have checked your document requirements.';
      error.textContent=message; return !message;
    }
    review.hidden=false; confirm.hidden=true;
    review.addEventListener('click',()=>{
      if (!validate()) { error.setAttribute('tabindex','-1'); error.focus(); return; }
      reviewed=true; panel.hidden=false; confirm.hidden=false; review.hidden=true; panel.focus();
    });
    form.querySelector('[data-edit-booking]').addEventListener('click',resetReview);
    docInputs.forEach(input=>input.addEventListener('change',()=>{ updateDocuments(); loadMonth(); }));
    form.querySelector('#id_prepared').addEventListener('change',resetReview);
    document.addEventListener('appointment:change',event=>{
      form.querySelector('[data-summary-date]').textContent=event.detail?.dateLabel || 'Not selected';
      form.querySelector('[data-summary-time]').textContent=event.detail?.slot.time || 'Not selected';
      resetReview();
    });
    // The fallback continues to work if loading the calendar fails.
    select.addEventListener('change',()=>{
      const option=select.selectedOptions[0];
      if (!fallback.hidden && select.value) { form.querySelector('[data-summary-date]').textContent=option.textContent; form.querySelector('[data-summary-time]').textContent='See appointment above'; resetReview(); }
    });
    form.addEventListener('submit',event=>{ if (!validate() || !reviewed) { event.preventDefault(); if (!error.textContent) error.textContent='Please review your appointment before confirming.'; } });
    const filter=form.querySelector('[data-document-filter]');
    filter.addEventListener('input',()=>docInputs.forEach(input=>{
      const row=input.closest('label').parentElement; row.hidden=!row.textContent.toLowerCase().includes(filter.value.toLowerCase());
    }));
    updateDocuments();
  }
  loadMonth(config.selectedSlot);
})();

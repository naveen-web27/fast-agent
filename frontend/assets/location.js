// Shared location UI: the Zomato-style location chip, a small "set location" card, and area/PIN autocomplete.
// Location is stored as a place { pincode, area, district, state }; searches send its PIN so nearby people come first.
(() => {
  const PLACE_KEY = 'rightconnect-place';
  const OLD_PIN_KEY = 'rightconnect-pincode';
  const API = '/api/v1';
  const NEAR_LABELS = { 4: 'In your area', 3: 'Same district', 2: 'Same state', 1: 'Nearby region' };

  const style = document.createElement('style');
  style.textContent = `
    .rc-loc { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin-top:3px; color:#526078; font-size:12px; }
    .rc-loc.missing { color:#9a6b00; font-style:italic; }
    .rc-near { padding:1px 7px; border-radius:999px; background:#e1f6ee; color:#0b6b4f; font-size:10px; font-weight:800; font-style:normal; }
    .rc-near.far { background:#eef2f6; color:#526078; }
    .rc-chip { display:inline-flex; align-items:center; gap:7px; max-width:280px; min-height:40px; padding:4px 12px 4px 8px; color:#142033; border:1px solid #e3e8f0; border-radius:10px; background:#fff; font:inherit; text-align:left; cursor:pointer; }
    .rc-chip:hover { border-color:#b8e5dc; background:#f6fbf9; }
    .rc-chip .rc-pin { font-size:18px; line-height:1; }
    .rc-chip .rc-chip-text { min-width:0; display:grid; line-height:1.2; }
    .rc-chip small { color:#6b7891; font-size:10px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
    .rc-chip strong { overflow:hidden; font-size:13px; white-space:nowrap; text-overflow:ellipsis; }
    .rc-chip.empty strong { color:#b45309; }
    .rc-chip .rc-caret { color:#6b7891; font-size:11px; }
    .rc-scrim { position:fixed; inset:0; z-index:1000; display:flex; align-items:flex-start; justify-content:center; padding:72px 14px 14px; background:rgba(16,27,49,.45); }
    .rc-card { width:min(460px,100%); max-height:calc(100vh - 100px); display:flex; flex-direction:column; overflow:hidden; border-radius:14px; background:#fff; color:#142033; box-shadow:0 30px 70px rgba(0,0,0,.25); font-family:inherit; }
    .rc-card-head { padding:18px 18px 10px; }
    .rc-card-head h2 { margin:0 0 3px; font-size:18px; }
    .rc-card-head p { margin:0; color:#6b7891; font-size:12px; }
    .rc-card-close { float:right; width:30px; height:30px; border:0; border-radius:8px; background:#f1f4f8; font-size:16px; cursor:pointer; }
    .rc-search { position:relative; padding:0 18px 12px; }
    .rc-search input { width:100%; min-height:46px; padding:0 14px 0 38px; border:1.5px solid #cfe3dc; border-radius:10px; outline:0; font:inherit; font-size:15px; background:#fff; color:inherit; box-sizing:border-box; }
    .rc-search input:focus { border-color:#0f9d8f; box-shadow:0 0 0 3px rgba(15,157,143,.12); }
    .rc-search::before { content:'⌕'; position:absolute; left:32px; top:12px; color:#6b7891; font-size:16px; }
    .rc-results { overflow:auto; padding:0 8px 12px; }
    .rc-option { display:flex; width:100%; align-items:center; justify-content:space-between; gap:10px; padding:10px; border:0; border-radius:9px; background:none; color:inherit; font:inherit; text-align:left; cursor:pointer; }
    .rc-option:hover,.rc-option:focus-visible { background:#f1faf6; outline:0; }
    .rc-option strong { display:block; font-size:14px; }
    .rc-option span { color:#6b7891; font-size:12px; }
    .rc-option em { flex:none; padding:2px 8px; border-radius:6px; background:#eef2f6; color:#33425e; font:700 12px ui-monospace,monospace; font-style:normal; }
    .rc-group { margin:10px 10px 2px; color:#6b7891; font-size:11px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
    .rc-note { margin:8px 10px; color:#6b7891; font-size:12px; }
    .rc-current { margin:0 18px 10px; padding:9px 11px; border-radius:9px; background:#f6f8fb; font-size:12px; }
    .rc-auto { position:relative; }
    .rc-auto-list { position:absolute; left:0; right:0; top:calc(100% + 4px); z-index:60; max-height:280px; overflow:auto; padding:4px; border:1px solid #e3e8f0; border-radius:10px; background:#fff; box-shadow:0 14px 30px rgba(16,27,49,.14); }
    .rc-auto-hint { display:block; margin-top:5px; color:#0b6b4f; font-size:12px; font-weight:700; }
    @media (max-width:720px) { .rc-chip { max-width:190px; } .rc-scrim { padding-top:20px; } }
  `;
  document.head.append(style);

  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const clean = (pin) => String(pin ?? '').replace(/\s/g, '');
  const valid = (pin) => /^[1-9][0-9]{5}$/.test(clean(pin));

  function readStored() {
    try {
      const place = JSON.parse(localStorage.getItem(PLACE_KEY) || 'null');
      if (place && valid(place.pincode)) return place;
    } catch (_) { /* Ignore a corrupt value. */ }
    const pin = localStorage.getItem(OLD_PIN_KEY);
    return valid(pin) ? { pincode: pin } : null;
  }

  function placeLabel(place) {
    if (!place) return '';
    const parts = [place.area, place.district].filter(Boolean);
    const unique = parts.filter((part, index) => parts.findIndex((other) => other.toLowerCase() === part.toLowerCase()) === index);
    return unique.join(', ') || place.pincode || '';
  }

  async function search(query) {
    const response = await fetch(`${API}/locations/search?${new URLSearchParams({ q: query })}`);
    if (!response.ok) throw new Error('Could not search places right now.');
    return response.json();
  }

  /** Renders results into a list element; calls onPick(place) when one is chosen. */
  function renderOptions(list, places, query, onPick) {
    list.innerHTML = '';
    let lastGroup = null;
    const groupFor = (place) => (place.matched_on === 'district' ? `Areas in ${place.district} district` : place.matched_on === 'taluk' ? `Areas in ${place.taluk} taluk` : null);
    places.forEach((place) => {
      const group = groupFor(place);
      if (group && group !== lastGroup) list.insertAdjacentHTML('beforeend', `<div class="rc-group">${escape(group)}</div>`);
      lastGroup = group;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'rc-option';
      const taluk = place.taluk && ![place.area, place.district].some((name) => name && name.toLowerCase() === place.taluk.toLowerCase()) ? place.taluk : null;
      const where = [taluk, place.district, place.state].filter(Boolean);
      button.innerHTML = `<div><strong>${escape(place.area)}</strong><span>${escape(where.join(', '))}</span></div><em>${escape(place.pincode)}</em>`;
      button.addEventListener('mousedown', (event) => event.preventDefault());
      button.addEventListener('click', () => onPick({ pincode: place.pincode, area: place.area, district: place.district, state: place.state }));
      list.appendChild(button);
    });
    const digits = clean(query);
    if (valid(digits) && !places.some((place) => place.pincode === digits)) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'rc-option';
      button.innerHTML = `<div><strong>Use PIN code ${escape(digits)}</strong><span>We couldn't find its area name, but nearby matching still works.</span></div>`;
      button.addEventListener('mousedown', (event) => event.preventDefault());
      button.addEventListener('click', () => onPick({ pincode: digits }));
      list.appendChild(button);
    }
    if (!list.children.length) {
      list.innerHTML = `<p class="rc-note">${query.trim().length < 2 ? 'Type your area, town or district, e.g. “Edappadi” or “Salem”. Or type your PIN code.' : 'No place found. Check the spelling or type your 6-digit PIN code.'}</p>`;
    }
  }

  /** Debounced place search wired to an input. isOpen() says whether Enter should pick from the list. */
  function liveSearch(input, list, onPick, isOpen = () => true) {
    let timer = null;
    let ticket = 0;
    let pending = false;
    const run = async () => {
      clearTimeout(timer);
      timer = null;
      const query = input.value.trim();
      const mine = ++ticket;
      pending = true;
      try {
        const places = query.length < 2 && !/^\d{3,}$/.test(clean(query)) ? [] : await search(query);
        if (mine === ticket) renderOptions(list, places, query, onPick);
      } catch (_) {
        if (mine === ticket) renderOptions(list, [], query, onPick);
      } finally {
        if (mine === ticket) pending = false;
      }
    };
    input.addEventListener('input', () => { clearTimeout(timer); pending = true; timer = setTimeout(run, 200); });
    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' || !isOpen()) return;
      event.preventDefault();
      // Pick from results for exactly what was typed, never from an older search.
      if (pending) run().then(() => { if (isOpen()) list.querySelector('.rc-option')?.click(); });
      else list.querySelector('.rc-option')?.click();
    });
    return { run, cancel() { clearTimeout(timer); timer = null; ticket += 1; pending = false; } };
  }

  let openCard = null;
  /** The small location card. onSave(place) may be async; the card closes once it succeeds. */
  function openPicker({ title = 'Choose your location', hint = 'We show experts, companies and workers near you first.', current = null, onSave }) {
    openCard?.remove();
    const scrim = document.createElement('div');
    scrim.className = 'rc-scrim';
    scrim.innerHTML = `<div class="rc-card" role="dialog" aria-modal="true" aria-labelledby="rc-card-title">
        <div class="rc-card-head"><button class="rc-card-close" type="button" aria-label="Close">✕</button><h2 id="rc-card-title">${escape(title)}</h2><p>${escape(hint)}</p></div>
        ${current && current.pincode ? `<div class="rc-current">Now: <strong>📍 ${escape(placeLabel(current))}</strong>${current.area || current.district ? ` · ${escape(current.pincode)}` : ''}</div>` : ''}
        <div class="rc-search"><input type="search" autocomplete="off" placeholder="Area, town, district or PIN code" aria-label="Area, town, district or PIN code"></div>
        <div class="rc-results"></div>
        <p class="rc-note rc-error" hidden style="color:#b4233f;margin:0 18px 12px"></p>
      </div>`;
    const input = scrim.querySelector('input');
    const list = scrim.querySelector('.rc-results');
    const error = scrim.querySelector('.rc-error');
    const onKey = (event) => { if (event.key === 'Escape') close(); };
    function close() { scrim.remove(); openCard = null; document.removeEventListener('keydown', onKey); }
    const pick = async (place) => {
      error.hidden = true;
      list.style.opacity = '.5';
      try {
        await onSave(place);
        close();
      } catch (problem) {
        list.style.opacity = '';
        error.textContent = problem.message || 'Could not save your location. Please try again.';
        error.hidden = false;
      }
    };
    scrim.addEventListener('click', (event) => { if (event.target === scrim) close(); });
    scrim.querySelector('.rc-card-close').addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    liveSearch(input, list, pick);
    renderOptions(list, [], '', pick);
    document.body.appendChild(scrim);
    openCard = scrim;
    input.focus();
  }

  /** Turns a plain input into an area/PIN autocomplete. The chosen place is kept on input.rcPlace. */
  function attach(input, { onPick } = {}) {
    if (!input || input.dataset.rcAttached) return;
    input.dataset.rcAttached = '1';
    input.setAttribute('autocomplete', 'off');
    input.removeAttribute('pattern');
    input.setAttribute('maxlength', '80');
    input.setAttribute('inputmode', 'text');
    input.placeholder = 'Type your area, town or PIN code';
    const wrap = document.createElement('div');
    wrap.className = 'rc-auto';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    const list = document.createElement('div');
    list.className = 'rc-auto-list';
    list.hidden = true;
    const hint = document.createElement('small');
    hint.className = 'rc-auto-hint';
    hint.hidden = true;
    wrap.append(list, hint);
    const show = (place) => {
      hint.hidden = !place;
      if (place) hint.textContent = `📍 ${placeLabel(place)}${place.state ? `, ${place.state}` : ''}${place.area || place.district ? ` · ${place.pincode}` : ''}`;
    };
    const choose = (place) => {
      searcher.cancel();
      input.rcPlace = place;
      input.value = place.area ? `${place.area} (${place.pincode})` : place.pincode;
      list.hidden = true;
      list.innerHTML = '';
      show(place);
      input.setCustomValidity('');
      onPick?.(place);
    };
    const initial = clean(input.value);
    if (valid(initial)) input.rcPlace = { pincode: initial };
    const searcher = liveSearch(input, list, choose, () => !list.hidden && !input.rcPlace);
    input.addEventListener('input', () => { input.rcPlace = null; show(null); list.hidden = false; });
    input.addEventListener('focus', () => { if (input.value.trim() && !input.rcPlace) { list.hidden = false; searcher.run(); } });
    input.addEventListener('blur', () => setTimeout(() => {
      list.hidden = true;
      const digits = clean(input.value);
      if (!input.rcPlace && valid(digits)) input.rcPlace = { pincode: digits };
    }, 150));
    if (valid(initial)) {
      window.RCLocation.describe(initial).then((place) => {
        if (place && input.rcPlace?.pincode === initial) { input.rcPlace = place; show(place); }
      });
    }
  }

  window.RCLocation = {
    valid,
    clean,
    label: placeLabel,
    openPicker,
    attach,
    /** The chosen place from an attached input (or a typed 6-digit PIN), else null. */
    picked(input) {
      if (!input) return null;
      if (input.rcPlace) return input.rcPlace;
      const digits = clean(input.value);
      return valid(digits) ? { pincode: digits } : null;
    },
    /** The visitor's place: their account's if signed in, else the one chosen on this device. */
    place(account) {
      if (account && valid(account.pincode)) {
        const stored = readStored();
        if (stored && stored.pincode === account.pincode && stored.area) return stored;
        return { pincode: account.pincode, area: account.locality || null, district: account.city || null };
      }
      return readStored();
    },
    remember(place) {
      if (place && valid(place.pincode)) localStorage.setItem(PLACE_KEY, JSON.stringify(place));
      localStorage.removeItem(OLD_PIN_KEY);
    },
    get(account) { return this.place(account)?.pincode || ''; },
    /** Adds near/near_city so the API lists nearby people first. */
    apply(params, account) {
      const place = this.place(account);
      if (place && valid(place.pincode)) params.set('near', place.pincode);
      const city = (place && place.district) || (account && account.city);
      if (city) params.set('near_city', city);
      return params;
    },
    /** Top-bar location chip. getAccount() returns the signed-in account or null; onChange(place) saves it. */
    mountChip(container, { getAccount, onChange }) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'rc-chip';
      button.setAttribute('aria-label', 'Change your location');
      container.appendChild(button);
      const render = () => {
        const place = this.place(getAccount());
        button.classList.toggle('empty', !place);
        button.innerHTML = `<span class="rc-pin">📍</span><span class="rc-chip-text"><small>${place ? 'Your location' : 'Location'}</small><strong>${escape(place ? placeLabel(place) : 'Set your location')}</strong></span><span class="rc-caret">▾</span>`;
        // Fill in the area name when only a PIN is known (e.g. signed in on a new device).
        if (place && !place.area) {
          this.describe(place.pincode).then((full) => { if (full && this.get(getAccount()) === full.pincode) { this.remember(full); render(); } });
        }
      };
      const open = () => this.openPicker({
        current: this.place(getAccount()),
        onSave: async (place) => {
          const previous = readStored();
          this.remember(place);
          try {
            await onChange(place);
          } catch (problem) {
            if (previous) this.remember(previous); else localStorage.removeItem(PLACE_KEY);
            throw problem;
          }
          render();
        },
      });
      button.addEventListener('click', open);
      render();
      return { render, open };
    },
    async describe(pincode) {
      try {
        const response = await fetch(`${API}/locations/${clean(pincode)}`);
        const places = response.ok ? await response.json() : [];
        return places[0] ? { pincode: places[0].pincode, area: places[0].area, district: places[0].district, state: places[0].state } : null;
      } catch (_) { return null; }
    },
    text(item) {
      const area = item.locality || item.area;
      const parts = [area, item.city].filter(Boolean);
      const unique = parts.filter((part, index) => parts.findIndex((other) => other.toLowerCase() === part.toLowerCase()) === index);
      return [unique.join(', '), item.pincode].filter(Boolean).join(' · ');
    },
    /** The 📍 line for any profile, worker or job card; flags a missing location instead of hiding it. */
    html(item, missingText = 'Location not added') {
      const text = this.text(item);
      const near = NEAR_LABELS[item.nearness];
      const badge = near ? `<span class="rc-near">${escape(near)}</span>` : (item.nearness === 0 ? '<span class="rc-near far">Far from you</span>' : '');
      return text ? `<div class="rc-loc">📍 ${escape(text)}${badge}</div>` : `<div class="rc-loc missing">📍 ${escape(missingText)}</div>`;
    },
  };
})();

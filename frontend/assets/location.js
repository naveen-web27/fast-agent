// Shared location helpers: the visitor's PIN code, the 📍 line on cards, and "near you" badges.
(() => {
  const KEY = 'rightconnect-pincode';
  const NEAR_LABELS = { 4: 'In your area', 3: 'Same district', 2: 'Same state', 1: 'Nearby region' };
  const style = document.createElement('style');
  style.textContent = `
    .rc-loc { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin-top:3px; color:#526078; font-size:12px; }
    .rc-loc.missing { color:#9a6b00; font-style:italic; }
    .rc-near { padding:1px 7px; border-radius:999px; background:#e1f6ee; color:#0b6b4f; font-size:10px; font-weight:800; font-style:normal; }
    .rc-near.far { background:#eef2f6; color:#526078; }
  `;
  document.head.append(style);

  function escape(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  }
  function clean(pin) { return String(pin ?? '').replace(/\s/g, ''); }

  window.RCLocation = {
    valid(pin) { return /^[1-9][0-9]{5}$/.test(clean(pin)); },
    clean,
    /** The visitor's PIN: their account's if signed in, else the one they typed on this device. */
    get(account) { return (account && account.pincode) || localStorage.getItem(KEY) || ''; },
    set(pin) {
      const value = clean(pin);
      if (this.valid(value)) localStorage.setItem(KEY, value);
      else if (!value) localStorage.removeItem(KEY);
    },
    /** Adds near/near_city to a URLSearchParams so the API lists nearby people first. */
    apply(params, account) {
      const pin = this.get(account);
      if (this.valid(pin)) params.set('near', pin);
      const city = account && account.city;
      if (city) params.set('near_city', city);
      return params;
    },
    text(item) {
      const place = [item.area, item.city].filter(Boolean).join(', ');
      return [place, item.pincode].filter(Boolean).join(' · ');
    },
    /** The 📍 line for any profile, worker or job card; flags a missing location instead of hiding it. */
    html(item, missingText = 'Location not added') {
      const text = this.text(item);
      const near = NEAR_LABELS[item.nearness];
      const badge = near ? `<span class="rc-near">${escape(near)}</span>` : (item.nearness === 0 ? '<span class="rc-near far">Far from you</span>' : '');
      return text
        ? `<div class="rc-loc">📍 ${escape(text)}${badge}</div>`
        : `<div class="rc-loc missing">📍 ${escape(missingText)}</div>`;
    },
  };
})();

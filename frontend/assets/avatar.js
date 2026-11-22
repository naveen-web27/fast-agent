// Generated avatars: a unique, stable two-tone badge for anyone without a photo or logo.
// The same id always gives the same colours and shapes; a small corner mark shows expert / company / worker.
(() => {
  const PALETTES = [
    ['#0f9d8f', '#16325c'], ['#ff7a59', '#b4235a'], ['#f5a623', '#e4572e'], ['#6c5ce7', '#2d1b69'],
    ['#00b894', '#0b6e4f'], ['#e84393', '#6c2bd9'], ['#0984e3', '#1e2a78'], ['#20bf6b', '#0f6f63'],
    ['#fd9644', '#c0392b'], ['#8854d0', '#3b2a8f'], ['#2bcbba', '#1170a8'], ['#eb3b5a', '#7a1f3d'],
  ];
  // 24x24 glyphs drawn inside the corner badge.
  const MARKS = {
    expert: '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.1 1.2 6-5.4-3-5.4 3 1.2-6L3.3 9.3l6.1-.7z"/>',
    company: '<path d="M5 21V5.5L13 3v18zm9 0V9l5 1.6V21zM7.5 8h2v2h-2zm0 4h2v2h-2zm0 4h2v2h-2zm8.5-2h1.5v1.5H16zm0 3h1.5v1.5H16z"/>',
    worker: '<path d="M4 16a8 8 0 0 1 16 0h1.5v2.5h-19V16zM11 6h2v5h-2z"/>',
    customer: '',
  };

  function hash(text) {
    let value = 2166136261;
    for (const char of String(text)) {
      value ^= char.codePointAt(0);
      value = Math.imul(value, 16777619);
    }
    return value >>> 0;
  }
  function initials(name) {
    const words = String(name || '').replace(/[^\p{L}\p{N}\s]/gu, ' ').split(/\s+/).filter(Boolean);
    if (!words.length) return '?';
    const letters = words.length === 1 ? [[...words[0]][0]] : [[...words[0]][0], [...words[words.length - 1]][0]];
    return letters.join('').toUpperCase();
  }
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  let counter = 0;

  /** SVG markup that fills its container. seed should be the profile/user id (name is used when missing). */
  function svg({ name, seed, kind = 'customer', round = false }) {
    const h = hash(seed || name || '?');
    const [from, to] = PALETTES[h % PALETTES.length];
    const id = `rcav${(counter += 1)}`;
    const angle = (h >>> 4) % 360;
    const c1x = 15 + ((h >>> 8) % 70);
    const c2y = 20 + ((h >>> 14) % 60);
    const text = initials(name);
    const mark = MARKS[kind] || '';
    return `<svg class="rc-av" viewBox="0 0 100 100" role="img" aria-label="${escape(name || 'Profile')}" preserveAspectRatio="xMidYMid slice">
      <defs><linearGradient id="${id}" gradientTransform="rotate(${angle} .5 .5)"><stop offset="0" stop-color="${from}"/><stop offset="1" stop-color="${to}"/></linearGradient></defs>
      <rect width="100" height="100" rx="${round ? 50 : 0}" fill="url(#${id})"/>
      <circle cx="${c1x}" cy="-6" r="34" fill="#fff" opacity=".13"/>
      <circle cx="104" cy="${c2y}" r="26" fill="#fff" opacity=".1"/>
      <circle cx="${100 - c1x}" cy="108" r="30" fill="#000" opacity=".08"/>
      <text x="50" y="${mark ? 52 : 50}" dy=".35em" text-anchor="middle" fill="#fff" font-family="Manrope, Inter, system-ui, sans-serif" font-weight="800" font-size="${text.length > 1 ? 36 : 44}" letter-spacing="-1">${escape(text)}</text>
      ${mark ? `<g transform="translate(${round ? 62 : 66} ${round ? 62 : 66})"><circle cx="15" cy="15" r="16" fill="#fff"/><g transform="translate(4.2 4.2) scale(.9)" fill="${to}">${mark}</g></g>` : ''}
    </svg>`;
  }

  window.RCAvatar = {
    initials,
    svg,
    /** Photo/logo when present, else the generated avatar. */
    html({ url, name, seed, kind, round = false, safeUrl = (value) => value }) {
      return url ? `<img src="${escape(safeUrl(url))}" alt="${escape(name || '')}" loading="lazy">` : svg({ name, seed, kind, round });
    },
  };

  const style = document.createElement('style');
  style.textContent = '.rc-av { display:block; width:100%; height:100%; } .portrait:has(> .rc-av), .avatar:has(> .rc-av), .xp-logo:has(> .rc-av) { background:none; }';
  document.head.append(style);
})();

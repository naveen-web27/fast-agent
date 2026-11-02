(() => {
  const ua = navigator.userAgent;
  const android = /Android/i.test(ua);
  const ios = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const inApp = /median|gonative|; wv\)/i.test(ua) || document.referrer.startsWith('android-app://');
  if ((!android && !ios) || standalone || inApp) return;

  const dismissalKey = 'rightconnect-install-dismissed';
  try {
    if (localStorage.getItem(dismissalKey) === '1') return;
  } catch (error) {
    console.warn('RightConnect cannot read the install suggestion preference.', error);
  }

  const style = document.createElement('style');
  style.textContent = `
    .rc-install-banner { position:relative; z-index:1; display:flex; align-items:center; gap:12px; padding:14px max(16px,calc((100% - 1120px)/2)); color:#172033; background:#e5f6f2; border-bottom:1px solid #b5d8d1; font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .rc-install-copy { flex:1; min-width:0; }
    .rc-install-copy strong { display:block; }
    .rc-install-copy p { margin:4px 0 0; font-size:12px; }
    .rc-install-action { flex-shrink:0; display:inline-flex; align-items:center; min-height:44px; padding:8px 12px; border:1px solid #087b74; border-radius:8px; color:white; background:#087b74; text-decoration:none; font-weight:750; }
    .rc-install-dismiss { align-self:flex-start; flex-shrink:0; min-width:44px; min-height:44px; border:1px solid #9cbbb7; border-radius:8px; color:#172033; background:transparent; font:22px/1 sans-serif; cursor:pointer; }
    .rc-install-banner a:focus-visible,.rc-install-banner button:focus-visible { outline:3px solid #d79212; outline-offset:3px; }
    @media (max-width:420px) { .rc-install-banner { flex-wrap:wrap; gap:8px; } .rc-install-copy { flex-basis:calc(100% - 60px); } .rc-install-dismiss { order:1; } .rc-install-action { order:2; } }
    @media print { .rc-install-banner { display:none; } }
  `;
  const banner = document.createElement('aside');
  banner.className = 'rc-install-banner';
  banner.lang = 'en';
  banner.setAttribute('aria-label', 'Install RightConnect');
  const copy = document.createElement('div');
  copy.className = 'rc-install-copy';
  const title = document.createElement('strong');
  title.textContent = android ? 'Take RightConnect with you' : 'Add RightConnect to your Home Screen';
  const description = document.createElement('p');
  description.textContent = android
    ? 'Download our Android APK, or keep using the website. Installation is optional.'
    : 'In Safari, tap Share (or More, then Share), then Add to Home Screen. No APK needed.';
  copy.append(title, description);
  const action = document.createElement('a');
  action.className = 'rc-install-action';
  action.textContent = android ? 'Download APK' : 'iPhone install help';
  action.href = android ? '/downloads/rightconnect.apk' : '/#iphone-install';
  if (android) action.download = 'RightConnect.apk';
  else action.addEventListener('click', () => dismiss());
  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'rc-install-dismiss';
  close.setAttribute('aria-label', 'Dismiss app install suggestion');
  close.textContent = '\u00d7';
  function dismiss() {
    try {
      localStorage.setItem(dismissalKey, '1');
    } catch (error) {
      console.warn('RightConnect cannot save the install suggestion preference.', error);
    }
    banner.remove();
    style.remove();
  }
  close.addEventListener('click', dismiss);
  banner.append(copy, action, close);
  document.head.append(style);
  (document.querySelector('[data-install-banner-host]') || document.body).prepend(banner);
})();

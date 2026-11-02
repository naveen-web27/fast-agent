(() => {
  const nav = (view) => `#sidebar [data-view="${view}"]`;
  const tours = {
    customer: [
      ['#search-input', 'Find the right help', 'Describe the service you need here, then use Search to find matching profiles.'],
      ['#kind-toggle', 'Choose experts or companies', 'Use these filters to choose which provider profiles appear.'],
      [nav('saved'), 'Keep a shortlist', 'Open a provider profile and save it for later. Your saved profiles appear here after sign-in.'],
      [nav('requests'), 'Track your requests', 'Open a provider profile to send a request. Return here to read replies and follow progress.'],
      [nav('dashboard'), 'Your overview', 'After sign-in, your dashboard brings together requests, meetings, and recommendations.'],
    ],
    expert: [
      ['#workspace-switcher', 'Your expert workspace', 'After sign-in, use Acting as to add or select your expert profile. This tour does not switch your identity.'],
      [nav('me'), 'Introduce your expertise', 'Use My profile in your expert workspace to open your profile and edit your services and experience.'],
      [nav('requests'), 'Respond to requests', 'In your expert workspace, use My requests to review incoming requests and reply.'],
      [nav('showcases'), 'Show your work', 'Use Manage my showcases to share YouTube or Instagram video links for your expert profile. Publishing requires profile ownership.'],
      [nav('dashboard'), 'Your expert overview', 'Select your expert workspace, then open Dashboard to see its activity and available actions.'],
    ],
    company: [
      ['#workspace-switcher', 'Choose your company workspace', 'After sign-in, use Acting as to select a company you belong to, or use the available company setup option. This tour does not create or switch a company.'],
      [nav('me'), 'Present your company services', 'My profile opens the selected company profile. Company admins can edit its details and services.'],
      [nav('requests'), 'Follow company enquiries', 'In your company workspace, use My requests to review conversations. Actions depend on your membership permissions.'],
      [nav('showcases'), 'Publish company showcases', 'Company admins can use Manage my showcases to share video links for the selected company profile.'],
      [nav('dashboard'), 'Your company overview', 'Select your company workspace, then open Dashboard for company activity and the management actions available to your role.'],
    ],
  };
  const style = document.createElement('style');
  style.textContent = `
    .sidebar { overflow-y:auto; }
    .rc-tour-shade { position:fixed; inset:0; z-index:1000; background:rgba(16,27,49,.55); }
    .rc-tour-ring { position:fixed; z-index:1001; pointer-events:none; border:3px solid #78e4c5; border-radius:8px; box-shadow:0 0 0 2px #172033; }
    .rc-tour-dialog { position:fixed; z-index:1002; width:min(360px,calc(100vw - 24px)); max-height:calc(100dvh - 24px); overflow:auto; padding:20px; border:1px solid #dce6f8; border-radius:14px; background:white; color:#172033; box-shadow:0 12px 48px rgba(0,0,0,.25); }
    .rc-tour-dialog h2 { margin:8px 0; font-size:20px; }
    .rc-tour-dialog p { line-height:1.6; }
    .rc-tour-actions { display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; }
    .rc-tour-dialog button:focus-visible { outline:3px solid #087b74; outline-offset:3px; }
  `;
  document.head.append(style);
  let active = null;
  let index = 0;
  let trigger = null;
  let target = null;
  const shade = document.createElement('div');
  shade.className = 'rc-tour-shade';
  const ring = document.createElement('div');
  ring.className = 'rc-tour-ring';
  ring.setAttribute('aria-hidden', 'true');
  const dialog = document.createElement('div');
  dialog.className = 'rc-tour-dialog';
  dialog.setAttribute('role', 'dialog');
  dialog.setAttribute('aria-modal', 'true');
  dialog.setAttribute('aria-labelledby', 'rc-tour-title');
  dialog.setAttribute('aria-describedby', 'rc-tour-copy');
  dialog.innerHTML = '<small id="rc-tour-progress"></small><h2 id="rc-tour-title"></h2><p id="rc-tour-copy"></p><div class="rc-tour-actions"><button type="button" class="secondary" data-tour-close>Exit tour</button><button type="button" class="secondary" data-tour-back>Back</button><button type="button" class="primary" data-tour-next>Next</button></div>';
  const next = dialog.querySelector('[data-tour-next]');
  const back = dialog.querySelector('[data-tour-back]');
  function position() {
    if (!active || !target) return;
    const box = target.getBoundingClientRect();
    Object.assign(ring.style, { left: `${box.left - 4}px`, top: `${box.top - 4}px`, width: `${box.width + 8}px`, height: `${box.height + 8}px` });
    const width = dialog.offsetWidth;
    const height = dialog.offsetHeight;
    const left = Math.max(12, Math.min(box.left, innerWidth - width - 12));
    const below = box.bottom + 14;
    const top = below + height <= innerHeight - 12 ? below : Math.max(12, box.top - height - 14);
    dialog.style.left = `${left}px`;
    dialog.style.top = `${top}px`;
  }
  function finish() {
    if (!active) return;
    active = null;
    target = null;
    shade.remove();
    ring.remove();
    dialog.remove();
    document.removeEventListener('keydown', onKey, true);
    window.removeEventListener('resize', position);
    window.removeEventListener('scroll', position, true);
    showView('app-tour');
    trigger?.focus();
  }
  function render() {
    const [selector, title, copy] = active[index];
    showView('discover');
    target = document.querySelector(selector);
    if (!target || target.hidden) {
      showToast('This tour control is unavailable. Please reload and try again.', 'error');
      finish();
      return;
    }
    const sidebarTarget = target.closest('#sidebar');
    document.querySelector('#sidebar').classList.toggle('open', !!sidebarTarget);
    document.querySelector('#sidebar-scrim').classList.toggle('open', !!sidebarTarget);
    target.scrollIntoView({ block: 'center', behavior: 'instant' });
    dialog.querySelector('#rc-tour-progress').textContent = `Step ${index + 1} of ${active.length}`;
    dialog.querySelector('#rc-tour-title').textContent = title;
    dialog.querySelector('#rc-tour-copy').textContent = copy;
    back.disabled = index === 0;
    next.textContent = index === active.length - 1 ? 'Finish tour' : 'Next';
    requestAnimationFrame(position);
    next.focus();
  }
  function onKey(event) {
    if (event.key === 'Escape') { event.preventDefault(); event.stopImmediatePropagation(); finish(); }
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('button:not(:disabled)')];
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
      event.preventDefault(); first.focus();
    }
  }
  dialog.querySelector('[data-tour-close]').addEventListener('click', finish);
  back.addEventListener('click', () => { if (index > 0) { index -= 1; render(); } });
  next.addEventListener('click', () => {
    if (index === active.length - 1) finish();
    else { index += 1; render(); }
  });
  document.querySelectorAll('[data-start-tour]').forEach((button) => {
    button.addEventListener('click', () => {
      if (active) return;
      trigger = button;
      active = tours[button.dataset.startTour];
      index = 0;
      document.body.append(shade, ring, dialog);
      document.addEventListener('keydown', onKey, true);
      window.addEventListener('resize', position);
      window.addEventListener('scroll', position, true);
      render();
    });
  });
})();

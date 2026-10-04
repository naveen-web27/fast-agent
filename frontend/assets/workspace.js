// Dashboards and provider tools for marketplace.html. Loaded after the page script and uses its globals
// (apiBase, accessToken, identities, authHeaders, escapeHtml, safeHref, showToast, openModal, closeModals, ...).

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const IST = 'Asia/Kolkata';
const ACTIVE_MEETING = ['proposed', 'confirmed'];

document.querySelectorAll('[data-close-modal]').forEach((button) => button.addEventListener('click', closeModals));

function actingAs() {
  return JSON.parse(sessionStorage.getItem('rightconnect-acting-as') || '{"type":"customer","label":"Customer"}');
}

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...authHeaders() },
  });
  if (!response.ok) throw new Error(await extractErrorMessage(response, 'Something went wrong. Please try again.'));
  return response.status === 204 ? null : response.json();
}

function formatWhen(iso) {
  return new Date(iso).toLocaleString('en-IN', { timeZone: IST, weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
}
function formatDate(iso) { return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }); }
function formatPrice(min, max) {
  const inr = (value) => `₹${Number(value).toLocaleString('en-IN')}`;
  if (min != null && max != null) return min === max ? inr(min) : `${inr(min)} – ${inr(max)}`;
  if (min != null) return `From ${inr(min)}`;
  if (max != null) return `Up to ${inr(max)}`;
  return 'Price on request';
}
function planLabel(plan) { return plan === 'pro' ? 'Pro' : 'Enterprise'; }
function emptyNote(text) { return `<p class="muted" style="margin:0">${text}</p>`; }

// Type-ahead for service areas: "beau" -> Beauty & wellness, Beauty salon, Beauty & fashion...
function attachSuggest(input, onPick) {
  const wrap = document.createElement('div');
  wrap.className = 'suggest-wrap';
  input.parentNode.insertBefore(wrap, input);
  wrap.appendChild(input);
  const list = document.createElement('div');
  list.className = 'suggest-list';
  list.hidden = true;
  list.setAttribute('role', 'listbox');
  wrap.appendChild(list);
  let timer = null;
  let ticket = 0;
  const load = () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const mine = ++ticket;
      let suggestions = [];
      try { suggestions = (await api(`/services/suggest?${new URLSearchParams({ q: input.value.trim() })}`)).suggestions; } catch (_) { /* typing still works */ }
      if (mine !== ticket || document.activeElement !== input) return;
      list.innerHTML = suggestions.map((item) => `<button type="button" role="option" data-value="${escapeHtml(item)}">${escapeHtml(item)}</button>`).join('');
      list.hidden = suggestions.length === 0;
      list.querySelectorAll('button').forEach((button) => button.addEventListener('mousedown', (event) => {
        event.preventDefault();
        list.hidden = true;
        onPick(button.dataset.value);
      }));
    }, 180);
  };
  input.setAttribute('autocomplete', 'off');
  input.addEventListener('input', load);
  input.addEventListener('focus', load);
  input.addEventListener('blur', () => { list.hidden = true; });
  input.addEventListener('keydown', (event) => { if (event.key === 'Escape') list.hidden = true; });
}

const interestsInput = document.querySelector('#interests-input');
attachSuggest(interestsInput, (value) => { interestsInput.value = value; document.querySelector('#interests-form').requestSubmit(); });
const needInput = document.querySelector('#need-input');
attachSuggest(needInput, (value) => { needInput.value = value; });
// Typing "ads" offers "Digital marketing"; picking one searches straight away.
const discoverSearchInput = document.querySelector('#search-input');
attachSuggest(discoverSearchInput, (value) => { discoverSearchInput.value = value; document.querySelector('#search-button').click(); });
document.querySelector('#interests-cancel').addEventListener('click', () => {
  if (document.querySelector('#dashboard').classList.contains('active')) loadDashboard();
});

/* ---------- Dashboards ---------- */

function kpi(label, value) { return `<div class="kpi"><small>${label}</small><strong>${value}</strong></div>`; }

function meetingRows(meetings, emptyText) {
  return meetings.length
    ? meetings.map((meeting) => `<div class="row"><span><strong>${escapeHtml(meeting.request_title)}</strong><br><span class="muted">with ${escapeHtml(meeting.with_name)}</span></span><button class="secondary" type="button" data-open-request="${escapeHtml(meeting.request_id)}">${escapeHtml(formatWhen(meeting.starts_at))}</button></div>`).join('')
    : emptyNote(emptyText);
}

function miniCard(profile) {
  return `<button type="button" class="mini-card" data-open-profile="${escapeHtml(profile.id)}"><strong>${escapeHtml(profile.display_name)}${profile.verified ? ' <span class="verified">●</span>' : ''}</strong><span>${escapeHtml(profile.headline)}</span><span>★ ${profile.average_rating.toFixed(1)} · ${profile.review_count} reviews · ${profile.kind}</span></button>`;
}

function wireDashboard() {
  const root = document.querySelector('#dashboard');
  root.querySelectorAll('[data-open-request]').forEach((button) => button.addEventListener('click', () => {
    setRequestsTab(actingAs().type === 'customer' ? 'sent' : 'received');
    showView('requests');
    selectRequest(button.dataset.openRequest);
    loadRequests({ silent: requestsCache.length > 0 });
  }));
  root.querySelectorAll('[data-open-profile]').forEach((button) => button.addEventListener('click', () => openProfile(button.dataset.openProfile)));
  root.querySelectorAll('[data-go]').forEach((button) => button.addEventListener('click', () => {
    if (button.dataset.go === 'requests') { document.querySelector('.nav-button[data-view="requests"]').click(); return; }
    showView(button.dataset.go);
  }));
  root.querySelectorAll('[data-edit-profile]').forEach((button) => button.addEventListener('click', (event) => {
    event.preventDefault();
    openProfileEditor(button.dataset.editProfile, button.dataset.focus);
  }));
  root.querySelectorAll('[data-team]').forEach((button) => button.addEventListener('click', () => openTeam(button.dataset.team)));
  root.querySelectorAll('[data-interests]').forEach((button) => button.addEventListener('click', () => { renderInterestsModal(); openModal('interests-modal'); }));
  root.querySelectorAll('[data-new-need]').forEach((button) => button.addEventListener('click', openNeedModal));
}

async function loadDashboard() {
  const body = document.querySelector('#dash-body');
  document.querySelector('#dash-actions').innerHTML = '';
  if (!accessToken) {
    body.innerHTML = '<div class="empty"><h2>Sign in to see your dashboard.</h2><p>Track requests, meetings and recommendations in one place.</p><a class="primary" style="margin-top:18px" href="auth.html">Sign in or join</a></div>';
    return;
  }
  body.innerHTML = '<p class="muted"><span class="spinner"></span>Loading your dashboard…</p>';
  const acting = actingAs();
  try {
    if (acting.type === 'expert') renderProviderDashboard(await api('/dashboard/expert'));
    else if (acting.type === 'company' && acting.id) renderProviderDashboard(await api(`/dashboard/company/${encodeURIComponent(acting.id)}`));
    else renderCustomerDashboard(await api('/dashboard/customer'));
  } catch (error) {
    body.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

function renderCustomerDashboard(data) {
  document.querySelector('#dash-tag').textContent = 'Dashboard';
  document.querySelector('#dash-title').textContent = currentUser?.full_name ? `Hi ${currentUser.full_name.split(' ')[0]}` : 'Your dashboard';
  document.querySelector('#dash-copy').textContent = '';
  document.querySelector('#dash-actions').innerHTML = '<button class="secondary" type="button" data-interests>Interests</button><button class="primary" type="button" data-go="discover">+ New request</button>';
  const counts = data.requests;
  const recommendations = data.recommendations.length
    ? data.recommendations.map((group) => `<h3 style="margin:10px 0 0;font-size:13px">${escapeHtml(group.interest)}</h3>${group.profiles.length
      ? `<div class="mini-cards">${group.profiles.map(miniCard).join('')}</div>`
      : `<p class="muted" style="margin:4px 0 12px">No one for ${escapeHtml(group.interest)} yet.</p>`}`).join('')
    : `${emptyNote('Add what you need and we will suggest people.')}<button class="primary" type="button" data-interests style="margin-top:12px">Add interests</button>`;
  document.querySelector('#dash-body').innerHTML = `
    ${currentUser && currentUser.looking_for_help === false ? '<div class="plan-banner free"><span>Your last need is done.</span><button class="primary" type="button" data-new-need>New need</button></div>' : ''}
    ${data.pending_actions ? `<div class="plan-banner free"><span>${data.pending_actions} need${data.pending_actions === 1 ? 's' : ''} your action</span><button class="primary" type="button" data-go="requests">Open</button></div>` : ''}
    <div class="kpi-grid">${kpi('Active', counts.active)}${kpi('Waiting', counts.waiting)}${kpi('Done', counts.completed)}${kpi('Saved', data.saved_count)}</div>
    <div class="dash-grid">
      <div class="dash-card"><h2>Meetings</h2>${meetingRows(data.upcoming_meetings, 'No meetings yet.')}</div>
      <div class="dash-card"><h2>How it works</h2><div class="row"><span>1. Search</span></div><div class="row"><span>2. Send request (free)</span></div><div class="row"><span>3. Chat &amp; book a time</span></div><div class="row"><span>4. Mark done &amp; rate</span></div></div>
      <div class="dash-card full"><h2>For you</h2>${recommendations}</div>
    </div>`;
  wireDashboard();
}

function renderBars(months) {
  const max = Math.max(1, ...months.map((item) => item.count));
  return `<div class="bars">${months.map((item) => {
    const [year, month] = item.month.split('-').map(Number);
    const label = new Date(year, month - 1, 1).toLocaleString('en-IN', { month: 'short' });
    return `<div>${item.count}<i style="height:${Math.round((item.count / max) * 80)}%"></i>${label}</div>`;
  }).join('')}</div>`;
}

function renderProviderDashboard(data) {
  const isCompany = data.kind === 'company';
  const canManage = !isCompany || data.member_role === 'admin';
  const plan = planLabel(data.plan);
  document.querySelector('#dash-tag').textContent = isCompany ? `Company dashboard · ${data.member_role}` : 'Expert dashboard';
  document.querySelector('#dash-title').textContent = data.name;
  document.querySelector('#dash-copy').textContent = isCompany && !canManage ? 'Requests assigned to you and your upcoming meetings.' : 'Leads, meetings and how your profile is doing.';
  document.querySelector('#dash-actions').innerHTML = [
    data.profile_id ? `<button class="secondary" type="button" data-open-profile="${escapeHtml(data.profile_id)}">View public profile</button>` : '',
    isCompany ? `<button class="secondary" type="button" data-team="${escapeHtml(data.organization_id)}">Team</button>` : '',
    canManage && data.profile_id ? `<button class="primary" type="button" data-edit-profile="${escapeHtml(data.profile_id)}">Edit profile</button>` : '',
  ].join('');

  const banner = data.plan_active
    ? `<div class="plan-banner"><span>✓ ${plan} active until ${formatDate(data.plan_expires_at)}</span>${canManage ? '<a class="secondary" href="plans.html">Add 30 days</a>' : ''}</div>`
    : `<div class="plan-banner free"><span>You're on Free. ${plan} adds online booking, a richer profile${isCompany ? ', team seats, request assignment' : ''} and insights.</span>${canManage ? `<a class="primary" href="plans.html">Upgrade to ${plan}</a>` : ''}</div>`;

  const completeness = data.completeness;
  const availabilityNote = !data.plan_active
    ? `<p class="muted" style="margin:10px 0 0">Online booking is part of ${plan}.</p>`
    : data.has_availability
      ? `<p class="muted" style="margin:10px 0 0">✓ Customers can book your open slots.${canManage ? ` <a href="#" data-edit-profile="${escapeHtml(data.profile_id)}" data-focus="availability">Change availability</a>` : ''}</p>`
      : `${canManage ? `<button class="primary" type="button" style="margin-top:10px" data-edit-profile="${escapeHtml(data.profile_id)}" data-focus="availability">Set weekly availability</button>` : ''}`;

  let insights;
  if (data.insights) {
    const ins = data.insights;
    insights = `
      <div class="dash-card full"><h2>Insights</h2>
        <div class="kpi-grid">${kpi('Profile views', ins.profile_views)}${kpi('Accept rate', ins.accept_rate == null ? '–' : `${ins.accept_rate}%`)}${kpi('Avg. time to accept', ins.avg_response_minutes == null ? '–' : ins.avg_response_minutes < 120 ? `${ins.avg_response_minutes} min` : `${Math.round(ins.avg_response_minutes / 60)} h`)}${kpi('Resolved clients', data.resolved_clients)}</div>
        <div class="dash-grid"><div><strong style="font-size:12px">Leads in the last 6 months</strong>${renderBars(ins.leads_by_month)}</div>
        <div><strong style="font-size:12px">Clients by domain</strong>${ins.clients_by_domain.length ? ins.clients_by_domain.map((item) => `<div class="row"><span>${escapeHtml(item.domain)}</span><strong>${item.count}</strong></div>`).join('') : emptyNote('Completed requests will show here.')}</div></div>
      </div>
      ${ins.pipeline ? `<div class="dash-card full"><h2>Pipeline</h2><div class="pipeline"><div><strong>${ins.pipeline.unassigned}</strong><small>Unassigned</small></div><div><strong>${ins.pipeline.assigned}</strong><small>Assigned</small></div><div><strong>${ins.pipeline.meeting_booked}</strong><small>Meeting booked</small></div><div><strong>${ins.pipeline.completed}</strong><small>Completed</small></div></div></div>` : ''}
      ${ins.team ? `<div class="dash-card full"><h2>Team performance</h2>${ins.team.map((member) => `<div class="row"><span><strong>${escapeHtml(member.full_name)}</strong> <span class="muted">${member.member_role}</span></span><span>${member.open} open · ${member.completed} completed</span></div>`).join('')}<button class="secondary" type="button" style="margin-top:10px" data-team="${escapeHtml(data.organization_id)}">Manage team</button></div>` : ''}`;
  } else {
    insights = `<div class="dash-card full locked-card"><h2>🔒 Insights with ${plan}</h2><ul>${data.locked_insights.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>${canManage ? `<a class="primary" href="plans.html">Upgrade to ${plan}</a>` : ''}</div>`;
  }

  document.querySelector('#dash-body').innerHTML = `
    ${banner}
    <div class="kpi-grid">${kpi('New leads waiting', data.leads.waiting)}${kpi('In progress', data.leads.active)}${kpi('Completed', data.leads.completed)}${kpi('Rating', data.review_count ? `★ ${data.average_rating.toFixed(1)} <small class="muted">(${data.review_count})</small>` : '–')}</div>
    <div class="dash-grid">
      <div class="dash-card"><h2>Profile strength · ${completeness.percent}%</h2><div class="progress"><i style="width:${completeness.percent}%"></i></div>
        ${completeness.missing.length ? `<p class="muted" style="margin:10px 0 4px">Complete profiles get more requests. Add:</p>${completeness.missing.map((item) => `<div class="row"><span>${escapeHtml(item)}</span></div>`).join('')}` : '<p class="muted" style="margin:10px 0 0">✓ Your profile is complete.</p>'}
        ${canManage && completeness.missing.length ? `<button class="secondary" type="button" style="margin-top:10px" data-edit-profile="${escapeHtml(data.profile_id)}">Complete profile</button>` : ''}</div>
      <div class="dash-card"><h2>Upcoming meetings</h2>${meetingRows(data.upcoming_meetings, 'No meetings booked yet.')}${availabilityNote}</div>
      ${data.leads.waiting ? `<div class="dash-card full"><h2>${data.leads.waiting} customer${data.leads.waiting === 1 ? ' is' : 's are'} waiting for you</h2><p class="muted" style="margin:0 0 10px">Fast replies win more customers.</p><button class="primary" type="button" data-go="requests">Open requests</button></div>` : ''}
      ${insights}
    </div>`;
  wireDashboard();
}

/* ---------- Profile editor ---------- */

const TEAM_SIZES = ['1-10', '11-50', '51-200', '201-500', '500+'];
let editorProfile = null;
let editorServices = [];
let editorKeywords = [];
let editorWindows = [];

async function openProfileEditor(profileId, focus) {
  const body = document.querySelector('#editor-body');
  body.innerHTML = '<p class="muted"><span class="spinner"></span>Loading…</p>';
  openModal('editor-modal');
  try {
    renderEditor(await api(`/profiles/${encodeURIComponent(profileId)}/manage`));
    if (focus) document.querySelector(`#editor-${focus}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    body.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

function field(id, label, value, attrs = '') {
  return `<div class="field"><label for="${id}">${label}</label><input id="${id}" value="${escapeHtml(value ?? '')}" ${attrs}></div>`;
}

function renderEditor(profile) {
  editorProfile = profile;
  editorServices = [...profile.services];
  editorKeywords = [...profile.keywords];
  editorWindows = profile.availability.map((window) => ({ weekday: window.weekday, start_time: window.start_time.slice(0, 5), end_time: window.end_time.slice(0, 5) }));
  const paid = profile.plan_active;
  const plan = planLabel(profile.plan);
  const lock = paid ? '' : `<span class="lock-pill">🔒 ${plan}</span>`;
  const upgrade = `<p class="muted" style="margin:0">Part of ${plan}. <a href="plans.html">Upgrade</a> to unlock it.</p>`;
  document.querySelector('#editor-title').textContent = `Edit ${profile.kind === 'company' ? 'company' : 'expert'} profile`;
  document.querySelector('#editor-body').innerHTML = `
    <section class="editor-section"><h3>Basics <span class="muted">Free</span></h3>
      <form id="editor-basics">
        <div class="editor-grid">
          ${field('ed-name', profile.kind === 'company' ? 'Company name' : 'Display name', profile.display_name, 'required minlength="2" maxlength="160"')}
          ${field('ed-headline', 'Headline', profile.headline, 'required minlength="2" maxlength="160" placeholder="e.g. Health insurance advisor for families"')}
          ${field('ed-city', 'City', profile.city, 'maxlength="100"')}
          ${profile.kind === 'expert' ? field('ed-years', 'Years of experience', profile.years_experience, 'type="number" min="0" max="80"') : ''}
          ${profile.kind === 'company' ? field('ed-founded', 'Founded (year)', profile.founded_year, 'type="number" min="1800" max="2100" placeholder="2015"') : ''}
          ${profile.kind === 'company' ? `<div class="field"><label for="ed-team-size">Team size</label><select id="ed-team-size"><option value="">Not set</option>${TEAM_SIZES.map((size) => `<option value="${size}" ${profile.team_size === size ? 'selected' : ''}>${size} people</option>`).join('')}</select></div>` : ''}
          ${field('ed-languages', 'Languages (comma separated)', profile.languages.join(', '), 'placeholder="English, Tamil"')}
          ${field('ed-avatar', 'Photo or logo link', profile.avatar_url, 'type="url" placeholder="https://"')}
        </div>
        <div class="field"><label for="ed-bio">About</label><textarea id="ed-bio" rows="3" maxlength="2000">${escapeHtml(profile.bio ?? '')}</textarea></div>
        <div class="field"><label for="ed-service-input">Services you offer</label><div class="tag-list" id="ed-services"></div><input id="ed-service-input" placeholder="Type a service, e.g. beauty, then pick or press Enter"></div>
        <div class="field"><div class="q-head"><label for="ed-keyword-input">Search words</label><button type="button" class="info" aria-expanded="false" aria-controls="info-keywords" aria-label="About search words">i</button></div><p class="info-text" id="info-keywords" hidden>Words customers may type to find you, e.g. ads, facebook ads, leads. Not shown on your profile. Up to 20.</p><div class="tag-list" id="ed-keywords"></div><input id="ed-keyword-input" maxlength="40" placeholder="Type a word and press Enter"><div class="tag-list" id="ed-keyword-suggest" style="margin-top:6px"></div></div>
        <div class="editor-grid">
          ${field('ed-video', `Intro video link ${lock}`, profile.intro_video_url, `type="url" placeholder="https://youtube.com/..." ${paid ? '' : 'disabled'}`)}
          ${field('ed-portfolio', `Portfolio link ${lock}`, profile.portfolio_url, `type="url" placeholder="https://" ${paid ? '' : 'disabled'}`)}
        </div>
        <div class="modal-actions"><button class="primary" type="submit" id="ed-basics-save">Save basics</button></div>
      </form>
    </section>
    ${profile.kind === 'expert' ? `<section class="editor-section" id="editor-experience"><h3>Experience <span class="muted">Free</span></h3>
      ${profile.experiences.map((xp) => `<div class="item-row"><span><strong>${escapeHtml(xp.title)}</strong> · ${escapeHtml(xp.organization)} <span class="muted">· ${monthYear(xp.start_date)} – ${xp.end_date ? monthYear(xp.end_date) : 'Present'}</span></span><span style="display:flex;gap:6px"><button class="secondary" type="button" data-edit-exp="${escapeHtml(xp.id)}">Edit</button><button class="secondary" type="button" data-remove-exp="${escapeHtml(xp.id)}">Remove</button></span></div>`).join('')}
      <form id="editor-exp" style="margin-top:8px"><input type="hidden" id="ed-exp-id">
        <div class="editor-grid">
          ${field('ed-exp-title', 'Title', '', 'required minlength="2" maxlength="160" placeholder="e.g. Senior insurance advisor"')}
          ${field('ed-exp-org', 'Company or organisation', '', 'required maxlength="160"')}
          ${field('ed-exp-location', 'Location', '', 'maxlength="100" placeholder="Chennai or Remote"')}
          <div class="field"><label for="ed-exp-start">Started</label><input id="ed-exp-start" type="month" required placeholder="YYYY-MM"></div>
          <div class="field"><label for="ed-exp-end">Ended</label><input id="ed-exp-end" type="month" placeholder="YYYY-MM"></div>
          <label class="field" style="display:flex;align-items:center;gap:8px;align-self:end"><input type="checkbox" id="ed-exp-current" style="width:auto"> I work here now</label>
        </div>
        <div class="field"><label for="ed-exp-desc">What you did</label><textarea id="ed-exp-desc" rows="3" maxlength="2000" placeholder="Responsibilities, results, clients helped"></textarea></div>
        <div class="modal-actions"><button class="secondary" type="button" id="ed-exp-cancel" hidden>Cancel</button><button class="primary" type="submit" id="ed-exp-save">Add role</button></div>
      </form>
    </section>
    <section class="editor-section" id="editor-education"><h3>Education <span class="muted">Free</span></h3>
      ${profile.educations.map((edu) => `<div class="item-row"><span><strong>${escapeHtml(edu.school)}</strong>${edu.degree ? ` · ${escapeHtml(edu.degree)}` : ''} <span class="muted">${[edu.start_year, edu.end_year].filter(Boolean).join(' – ')}</span></span><span style="display:flex;gap:6px"><button class="secondary" type="button" data-edit-edu="${escapeHtml(edu.id)}">Edit</button><button class="secondary" type="button" data-remove-edu="${escapeHtml(edu.id)}">Remove</button></span></div>`).join('')}
      <form id="editor-edu" style="margin-top:8px"><input type="hidden" id="ed-edu-id">
        <div class="editor-grid">
          ${field('ed-edu-school', 'School, college or university', '', 'required minlength="2" maxlength="160"')}
          ${field('ed-edu-degree', 'Degree', '', 'maxlength="160" placeholder="e.g. MBA"')}
          ${field('ed-edu-field', 'Field of study', '', 'maxlength="160" placeholder="e.g. Finance"')}
          ${field('ed-edu-start', 'Start year', '', 'type="number" min="1900" max="2100"')}
          ${field('ed-edu-end', 'End year', '', 'type="number" min="1900" max="2100"')}
        </div>
        <div class="field"><label for="ed-edu-desc">Notes</label><textarea id="ed-edu-desc" rows="2" maxlength="1000" placeholder="Honours, projects, activities"></textarea></div>
        <div class="modal-actions"><button class="secondary" type="button" id="ed-edu-cancel" hidden>Cancel</button><button class="primary" type="submit" id="ed-edu-save">Add education</button></div>
      </form>
    </section>` : ''}
    <section class="editor-section" id="editor-links"><h3>Links <span class="muted">${profile.social_links.length}/${profile.limits.social_links}</span></h3>
      ${profile.social_links.map((link, index) => `<div class="item-row"><span style="display:flex;align-items:center;gap:8px;min-width:0">${linkIcon(link.url)}<strong>${escapeHtml(link.platform)}</strong> <a href="${safeHref(link.url)}" target="_blank" rel="noopener noreferrer" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(link.url)}</a></span><button class="secondary" type="button" data-remove-link="${index}">Remove</button></div>`).join('')}
      ${profile.social_links.length < profile.limits.social_links
        ? '<form id="editor-link" style="margin-top:8px"><div class="editor-grid"><div class="field" style="grid-column:1/-1"><label for="ed-link-url">Paste any link</label><input id="ed-link-url" required maxlength="500" autocomplete="off" placeholder="instagram.com/yourname, youtube.com/@channel, linkedin.com/in/you, yoursite.com"><span class="muted" id="ed-link-detect" style="display:flex;align-items:center;gap:6px;margin-top:6px;font-size:12px"></span></div><div class="field"><label for="ed-link-platform">Name (optional)</label><input id="ed-link-platform" maxlength="40" placeholder="We fill this in for you"></div></div><div class="modal-actions"><button class="secondary" type="submit">Add link</button></div></form>'
        : (paid ? '' : upgrade.replace('Part of', 'More links are part of'))}
    </section>
    <section class="editor-section" id="editor-credentials"><h3>Licences &amp; certifications <span class="muted">${profile.credentials.length}/${profile.limits.credentials}</span></h3>
      ${profile.credentials.map((credential) => `<div class="item-row"><span><strong>${escapeHtml(credential.title)}</strong>${credential.issuing_body ? ` · ${escapeHtml(credential.issuing_body)}` : ''} <span class="muted">· ${credential.verification === 'verified' ? '✓ verified' : credential.verification}</span></span><button class="secondary" type="button" data-remove-credential="${escapeHtml(credential.id)}">Remove</button></div>`).join('')}
      ${profile.credentials.length < profile.limits.credentials
        ? '<form id="editor-credential" style="margin-top:8px"><div class="editor-grid"><div class="field"><label for="ed-cred-title">Licence or certificate</label><input id="ed-cred-title" required minlength="2" maxlength="160" placeholder="IRDAI licensed agent"></div><div class="field"><label for="ed-cred-body">Issued by</label><input id="ed-cred-body" maxlength="160"></div><div class="field"><label for="ed-cred-number">Number</label><input id="ed-cred-number" maxlength="160"></div><div class="field"><label for="ed-cred-doc">Document link</label><input id="ed-cred-doc" type="url" placeholder="https://"></div></div><div class="modal-actions"><button class="secondary" type="submit">Add credential</button></div></form>'
        : (paid ? '' : upgrade.replace('Part of', 'More credentials are part of'))}
    </section>
    <section class="editor-section"><h3>Service catalogue &amp; prices ${lock}</h3>
      ${profile.offerings.map((offering) => `<div class="item-row"><span><strong>${escapeHtml(offering.title)}</strong> · <span class="price-tag">${formatPrice(offering.price_min_inr, offering.price_max_inr)}</span></span><button class="secondary" type="button" data-remove-offering="${escapeHtml(offering.id)}">Remove</button></div>`).join('')}
      ${paid
        ? '<form id="editor-offering" style="margin-top:8px"><div class="editor-grid"><div class="field" style="grid-column:1/-1"><label for="ed-off-title">Service</label><input id="ed-off-title" required minlength="2" maxlength="160" placeholder="Family health cover review"></div><div class="field"><label for="ed-off-min">Price from (₹)</label><input id="ed-off-min" type="number" min="0"></div><div class="field"><label for="ed-off-max">Price up to (₹)</label><input id="ed-off-max" type="number" min="0"></div></div><div class="field"><label for="ed-off-desc">What\'s included</label><textarea id="ed-off-desc" rows="2" maxlength="1000"></textarea></div><div class="modal-actions"><button class="secondary" type="submit">Add to catalogue</button></div></form>'
        : upgrade}
    </section>
    <section class="editor-section" id="editor-availability"><h3>Weekly availability for online booking ${lock}</h3>
      ${paid
        ? '<p class="muted" style="margin:0 0 10px">India time. Customers who sent you a request can book any free 30-minute slot in these windows.</p><div id="ed-windows"></div><div class="modal-actions" style="justify-content:space-between"><span><button class="secondary" type="button" id="ed-window-add">+ Add window</button> <button class="secondary" type="button" id="ed-window-preset">Mon–Fri 10:00–18:00</button></span><button class="primary" type="button" id="ed-window-save">Save availability</button></div>'
        : upgrade}
    </section>`;
  renderEditorServices();
  renderEditorKeywords();
  const keywordInput = document.querySelector('#ed-keyword-input');
  keywordInput.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ',') return;
    event.preventDefault();
    addEditorKeyword(keywordInput.value);
    keywordInput.value = '';
  });
  const serviceInput = document.querySelector('#ed-service-input');
  attachSuggest(serviceInput, addEditorService);
  serviceInput.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    addEditorService(serviceInput.value);
  });
  if (paid) renderWindows();
  wireEditor(profile);
}

function renderEditorKeywords() {
  const box = document.querySelector('#ed-keywords');
  box.innerHTML = editorKeywords.length
    ? editorKeywords.map((word, index) => `<span class="tag">${escapeHtml(word)}<button type="button" data-remove-keyword="${index}" aria-label="Remove ${escapeHtml(word)}">×</button></span>`).join('')
    : '<span class="muted">No search words yet.</span>';
  box.querySelectorAll('[data-remove-keyword]').forEach((button) => button.addEventListener('click', () => {
    editorKeywords.splice(Number(button.dataset.removeKeyword), 1);
    renderEditorKeywords();
  }));
  const suggestions = editorProfile.suggested_keywords.filter((word) => !editorKeywords.includes(word));
  const suggestBox = document.querySelector('#ed-keyword-suggest');
  suggestBox.innerHTML = suggestions.length
    ? `<span class="muted">Tap to add:</span> ${suggestions.map((word) => `<button type="button" class="pill" data-add-keyword="${escapeHtml(word)}">+ ${escapeHtml(word)}</button>`).join('')}`
    : '';
  suggestBox.querySelectorAll('[data-add-keyword]').forEach((button) => button.addEventListener('click', () => addEditorKeyword(button.dataset.addKeyword)));
}

function addEditorKeyword(value) {
  const word = value.replace(/,/g, ' ').trim().replace(/\s+/g, ' ').toLowerCase().slice(0, 40);
  if (!word || editorKeywords.includes(word)) return;
  if (editorKeywords.length >= 20) { showToast('You can add up to 20 search words.', 'error'); return; }
  editorKeywords.push(word);
  renderEditorKeywords();
}

function renderEditorServices() {
  const box = document.querySelector('#ed-services');
  box.innerHTML = editorServices.length
    ? editorServices.map((name, index) => `<span class="tag">${escapeHtml(name)}<button type="button" data-remove-service="${index}" aria-label="Remove ${escapeHtml(name)}">×</button></span>`).join('')
    : '<span class="muted">No services yet. Customers find you by these.</span>';
  box.querySelectorAll('[data-remove-service]').forEach((button) => button.addEventListener('click', () => {
    editorServices.splice(Number(button.dataset.removeService), 1);
    renderEditorServices();
  }));
}

function addEditorService(value) {
  const name = value.trim();
  const input = document.querySelector('#ed-service-input');
  input.value = '';
  if (!name || editorServices.some((item) => item.toLowerCase() === name.toLowerCase())) return;
  if (editorServices.length >= 10) { showToast('You can list up to 10 services.', 'error'); return; }
  editorServices.push(name.slice(0, 120));
  renderEditorServices();
}

function renderWindows() {
  const box = document.querySelector('#ed-windows');
  box.innerHTML = editorWindows.length
    ? editorWindows.map((window, index) => `<div class="window-row"><select data-window="${index}" data-key="weekday" aria-label="Day">${WEEKDAYS.map((day, value) => `<option value="${value}" ${value === window.weekday ? 'selected' : ''}>${day}</option>`).join('')}</select><input type="time" data-window="${index}" data-key="start_time" value="${window.start_time}" aria-label="From"><input type="time" data-window="${index}" data-key="end_time" value="${window.end_time}" aria-label="To"><button class="secondary" type="button" data-remove-window="${index}">Remove</button></div>`).join('')
    : emptyNote('No windows yet. Add the days and hours you take meetings.');
  box.querySelectorAll('[data-window]').forEach((input) => input.addEventListener('change', () => {
    const window = editorWindows[Number(input.dataset.window)];
    window[input.dataset.key] = input.dataset.key === 'weekday' ? Number(input.value) : input.value;
  }));
  box.querySelectorAll('[data-remove-window]').forEach((button) => button.addEventListener('click', () => {
    editorWindows.splice(Number(button.dataset.removeWindow), 1);
    renderWindows();
  }));
}

async function editorSave(button, path, method, payload, message) {
  setButtonLoading(button, true, 'Saving…');
  try {
    renderEditor(await api(path, { method, body: payload === undefined ? undefined : JSON.stringify(payload) }));
    showToast(message, 'success');
    if (document.querySelector('#dashboard').classList.contains('active')) loadDashboard();
    if (document.querySelector('#profile').classList.contains('active') && currentProfileId === editorProfile.id) openProfile(currentProfileId, { skipHistory: true });
  } catch (error) {
    setButtonLoading(button, false);
    showToast(error.message, 'error');
  }
}

function wireEditor(profile) {
  const base = `/profiles/${encodeURIComponent(profile.id)}`;
  const value = (id) => document.querySelector(id)?.value.trim() ?? '';
  document.querySelector('#editor-basics').addEventListener('submit', (event) => {
    event.preventDefault();
    addEditorKeyword(value('#ed-keyword-input'));
    const payload = {
      display_name: value('#ed-name'),
      headline: value('#ed-headline'),
      city: value('#ed-city') || null,
      languages: value('#ed-languages').split(',').map((item) => item.trim()).filter(Boolean),
      avatar_url: value('#ed-avatar') || null,
      bio: value('#ed-bio') || null,
      services: editorServices,
      keywords: editorKeywords,
    };
    if (profile.kind === 'expert') payload.years_experience = value('#ed-years') === '' ? null : Number(value('#ed-years'));
    if (profile.kind === 'company') {
      payload.founded_year = value('#ed-founded') === '' ? null : Number(value('#ed-founded'));
      payload.team_size = value('#ed-team-size') || null;
    }
    if (profile.plan_active) {
      payload.intro_video_url = value('#ed-video') || null;
      payload.portfolio_url = value('#ed-portfolio') || null;
    }
    editorSave(document.querySelector('#ed-basics-save'), base, 'PATCH', payload, 'Profile saved.');
  });
  const linkInput = document.querySelector('#ed-link-url');
  linkInput?.addEventListener('input', () => {
    const info = linkInfo(linkInput.value.trim());
    document.querySelector('#ed-link-detect').innerHTML = info.host ? `${linkIcon(linkInput.value.trim())} Shows as <strong>${escapeHtml(value('#ed-link-platform') || info.name)}</strong>` : '';
  });
  document.querySelector('#editor-link')?.addEventListener('submit', (event) => {
    event.preventDefault();
    const links = [...profile.social_links, { platform: value('#ed-link-platform') || null, url: value('#ed-link-url') }];
    editorSave(event.submitter, `${base}/social-links`, 'PUT', { links }, 'Link added.');
  });
  wireExperienceForm(profile, base, value);
  wireEducationForm(profile, base, value);
  document.querySelectorAll('[data-remove-link]').forEach((button) => button.addEventListener('click', () => {
    const links = profile.social_links.filter((_, index) => index !== Number(button.dataset.removeLink));
    editorSave(button, `${base}/social-links`, 'PUT', { links }, 'Link removed.');
  }));
  document.querySelector('#editor-credential')?.addEventListener('submit', (event) => {
    event.preventDefault();
    editorSave(event.submitter, `${base}/credentials`, 'POST', {
      title: value('#ed-cred-title'),
      issuing_body: value('#ed-cred-body') || null,
      credential_number: value('#ed-cred-number') || null,
      document_url: value('#ed-cred-doc') || null,
    }, 'Credential added. Our team will verify it.');
  });
  document.querySelectorAll('[data-remove-credential]').forEach((button) => button.addEventListener('click', () => {
    editorSave(button, `${base}/credentials/${encodeURIComponent(button.dataset.removeCredential)}`, 'DELETE', undefined, 'Credential removed.');
  }));
  document.querySelector('#editor-offering')?.addEventListener('submit', (event) => {
    event.preventDefault();
    const price = (id) => (value(id) === '' ? null : Number(value(id)));
    editorSave(event.submitter, `${base}/offerings`, 'POST', {
      title: value('#ed-off-title'),
      description: value('#ed-off-desc') || null,
      price_min_inr: price('#ed-off-min'),
      price_max_inr: price('#ed-off-max'),
    }, 'Added to your catalogue.');
  });
  document.querySelectorAll('[data-remove-offering]').forEach((button) => button.addEventListener('click', () => {
    editorSave(button, `${base}/offerings/${encodeURIComponent(button.dataset.removeOffering)}`, 'DELETE', undefined, 'Removed from your catalogue.');
  }));
  document.querySelector('#ed-window-add')?.addEventListener('click', () => {
    editorWindows.push({ weekday: 0, start_time: '10:00', end_time: '13:00' });
    renderWindows();
  });
  document.querySelector('#ed-window-preset')?.addEventListener('click', () => {
    editorWindows = [0, 1, 2, 3, 4].map((weekday) => ({ weekday, start_time: '10:00', end_time: '18:00' }));
    renderWindows();
  });
  document.querySelector('#ed-window-save')?.addEventListener('click', (event) => {
    editorSave(event.currentTarget, `${base}/availability`, 'PUT', { windows: editorWindows }, 'Availability saved. Customers can now book you.');
  });
}

// Month inputs give "YYYY-MM" (or free text where the browser has no month picker).
function monthToDate(value) {
  const match = /^(\d{4})-(\d{1,2})$/.exec(value);
  return match ? `${match[1]}-${match[2].padStart(2, '0')}-01` : null;
}

function wireExperienceForm(profile, base, value) {
  const form = document.querySelector('#editor-exp');
  if (!form) return;
  const current = document.querySelector('#ed-exp-current');
  const endInput = document.querySelector('#ed-exp-end');
  current.addEventListener('change', () => { endInput.disabled = current.checked; if (current.checked) endInput.value = ''; });
  const reset = () => {
    form.reset();
    document.querySelector('#ed-exp-id').value = '';
    endInput.disabled = false;
    document.querySelector('#ed-exp-save').textContent = 'Add role';
    document.querySelector('#ed-exp-cancel').hidden = true;
  };
  document.querySelector('#ed-exp-cancel').addEventListener('click', reset);
  document.querySelectorAll('[data-edit-exp]').forEach((button) => button.addEventListener('click', () => {
    const xp = profile.experiences.find((item) => item.id === button.dataset.editExp);
    document.querySelector('#ed-exp-id').value = xp.id;
    document.querySelector('#ed-exp-title').value = xp.title;
    document.querySelector('#ed-exp-org').value = xp.organization;
    document.querySelector('#ed-exp-location').value = xp.location ?? '';
    document.querySelector('#ed-exp-start').value = xp.start_date.slice(0, 7);
    endInput.value = xp.end_date ? xp.end_date.slice(0, 7) : '';
    current.checked = !xp.end_date;
    endInput.disabled = current.checked;
    document.querySelector('#ed-exp-desc').value = xp.description ?? '';
    document.querySelector('#ed-exp-save').textContent = 'Save role';
    document.querySelector('#ed-exp-cancel').hidden = false;
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }));
  document.querySelectorAll('[data-remove-exp]').forEach((button) => button.addEventListener('click', () => {
    if (!confirm('Remove this role?')) return;
    editorSave(button, `${base}/experiences/${encodeURIComponent(button.dataset.removeExp)}`, 'DELETE', undefined, 'Role removed.');
  }));
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const start = monthToDate(value('#ed-exp-start'));
    const end = current.checked ? null : monthToDate(value('#ed-exp-end'));
    if (!start) { showToast('Pick the month you started.', 'error'); return; }
    if (!current.checked && value('#ed-exp-end') && !end) { showToast('Pick the month you finished.', 'error'); return; }
    const id = value('#ed-exp-id');
    editorSave(document.querySelector('#ed-exp-save'), id ? `${base}/experiences/${encodeURIComponent(id)}` : `${base}/experiences`, id ? 'PUT' : 'POST', {
      title: value('#ed-exp-title'),
      organization: value('#ed-exp-org'),
      location: value('#ed-exp-location') || null,
      start_date: start,
      end_date: end,
      description: value('#ed-exp-desc') || null,
    }, id ? 'Role updated.' : 'Role added.');
  });
}

function wireEducationForm(profile, base, value) {
  const form = document.querySelector('#editor-edu');
  if (!form) return;
  const year = (id) => (value(id) === '' ? null : Number(value(id)));
  const reset = () => {
    form.reset();
    document.querySelector('#ed-edu-id').value = '';
    document.querySelector('#ed-edu-save').textContent = 'Add education';
    document.querySelector('#ed-edu-cancel').hidden = true;
  };
  document.querySelector('#ed-edu-cancel').addEventListener('click', reset);
  document.querySelectorAll('[data-edit-edu]').forEach((button) => button.addEventListener('click', () => {
    const edu = profile.educations.find((item) => item.id === button.dataset.editEdu);
    document.querySelector('#ed-edu-id').value = edu.id;
    document.querySelector('#ed-edu-school').value = edu.school;
    document.querySelector('#ed-edu-degree').value = edu.degree ?? '';
    document.querySelector('#ed-edu-field').value = edu.field_of_study ?? '';
    document.querySelector('#ed-edu-start').value = edu.start_year ?? '';
    document.querySelector('#ed-edu-end').value = edu.end_year ?? '';
    document.querySelector('#ed-edu-desc').value = edu.description ?? '';
    document.querySelector('#ed-edu-save').textContent = 'Save education';
    document.querySelector('#ed-edu-cancel').hidden = false;
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }));
  document.querySelectorAll('[data-remove-edu]').forEach((button) => button.addEventListener('click', () => {
    if (!confirm('Remove this education?')) return;
    editorSave(button, `${base}/educations/${encodeURIComponent(button.dataset.removeEdu)}`, 'DELETE', undefined, 'Education removed.');
  }));
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const id = value('#ed-edu-id');
    editorSave(document.querySelector('#ed-edu-save'), id ? `${base}/educations/${encodeURIComponent(id)}` : `${base}/educations`, id ? 'PUT' : 'POST', {
      school: value('#ed-edu-school'),
      degree: value('#ed-edu-degree') || null,
      field_of_study: value('#ed-edu-field') || null,
      start_year: year('#ed-edu-start'),
      end_year: year('#ed-edu-end'),
      description: value('#ed-edu-desc') || null,
    }, id ? 'Education updated.' : 'Education added.');
  });
}

/* ---------- Team seats ---------- */

async function openTeam(organizationId) {
  const body = document.querySelector('#team-body');
  body.innerHTML = '<p class="muted"><span class="spinner"></span>Loading…</p>';
  openModal('team-modal');
  try {
    renderTeam(await api(`/organizations/${encodeURIComponent(organizationId)}/team`));
  } catch (error) {
    body.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

function renderTeam(team) {
  const base = `/organizations/${encodeURIComponent(team.organization_id)}/team`;
  document.querySelector('#team-title').textContent = `${team.name} team`;
  const canInvite = team.can_manage && team.plan_active && team.seats_used < team.seat_limit;
  document.querySelector('#team-body').innerHTML = `
    ${team.plan_active ? '' : `<div class="plan-banner free"><span>Team seats and request assignment are part of Enterprise.</span>${team.can_manage ? '<a class="primary" href="plans.html">Upgrade</a>' : ''}</div>`}
    <p class="modal-note">${team.seats_used}/${team.seat_limit} seats used. Staff only see the requests you assign to them; admins see everything.</p>
    ${team.members.map((member) => `<div class="item-row"><span><strong>${escapeHtml(member.full_name)}</strong> <span class="muted">${escapeHtml(member.email)} · ${member.member_role} · ${member.open_assigned} open</span></span>${team.can_manage && member.member_role === 'staff' ? `<button class="secondary" type="button" data-remove-member="${escapeHtml(member.id)}">Remove</button>` : ''}</div>`).join('')}
    ${team.invites.map((invite) => `<div class="item-row"><span>${escapeHtml(invite.email)} <span class="muted">· invited ${formatDate(invite.created_at)}, joins on first sign-in</span></span>${team.can_manage ? `<button class="secondary" type="button" data-cancel-invite="${escapeHtml(invite.id)}">Cancel</button>` : ''}</div>`).join('')}
    ${canInvite ? '<form id="team-invite" style="display:flex;gap:8px;margin-top:12px"><input id="team-email" type="email" required placeholder="colleague@company.com" style="flex:1;padding:9px 10px;border:1px solid var(--line);border-radius:7px;font:inherit"><button class="primary" type="submit">Invite</button></form>' : ''}`;
  const act = async (button, path, method, payload, message) => {
    setButtonLoading(button, true, '…');
    try {
      renderTeam(await api(path, { method, body: payload ? JSON.stringify(payload) : undefined }));
      showToast(message, 'success');
    } catch (error) {
      setButtonLoading(button, false);
      showToast(error.message, 'error');
    }
  };
  document.querySelector('#team-invite')?.addEventListener('submit', (event) => {
    event.preventDefault();
    act(event.submitter, `${base}/invites`, 'POST', { email: document.querySelector('#team-email').value.trim() }, 'Invite sent.');
  });
  document.querySelectorAll('[data-remove-member]').forEach((button) => button.addEventListener('click', () => {
    if (confirm('Remove this person from the team? Their open requests go back to Unassigned.')) act(button, `${base}/members/${encodeURIComponent(button.dataset.removeMember)}`, 'DELETE', null, 'Removed from the team.');
  }));
  document.querySelectorAll('[data-cancel-invite]').forEach((button) => button.addEventListener('click', () => {
    act(button, `${base}/invites/${encodeURIComponent(button.dataset.cancelInvite)}`, 'DELETE', null, 'Invite cancelled.');
  }));
}

/* ---------- Requests: meetings, booking and assignment ---------- */

async function openBooking(requestId, profileId, name) {
  document.querySelector('#booking-title').textContent = `Pick a time · ${name}`;
  const body = document.querySelector('#booking-body');
  body.innerHTML = '<p class="muted"><span class="spinner"></span>Finding open times…</p>';
  openModal('booking-modal');
  try {
    const data = await api(`/requests/${encodeURIComponent(requestId)}/slots?${new URLSearchParams({ profile_id: profileId })}`);
    if (!data.slots.length) {
      body.innerHTML = emptyNote('No free times in the next 2 weeks. Message them to agree a time.');
      return;
    }
    const days = new Map();
    data.slots.forEach((slot) => {
      const day = new Date(slot).toLocaleDateString('en-IN', { timeZone: IST, weekday: 'long', day: 'numeric', month: 'short' });
      if (!days.has(day)) days.set(day, []);
      days.get(day).push(slot);
    });
    body.innerHTML = [...days.entries()].map(([day, slots]) => `<div class="slot-day"><strong>${day}</strong><div class="slot-grid">${slots.map((slot) => `<button type="button" data-slot="${escapeHtml(slot)}">${new Date(slot).toLocaleTimeString('en-IN', { timeZone: IST, hour: 'numeric', minute: '2-digit' })}</button>`).join('')}</div></div>`).join('');
    body.querySelectorAll('[data-slot]').forEach((button) => button.addEventListener('click', async () => {
      setButtonLoading(button, true, '');
      try {
        const detail = await api(`/requests/${encodeURIComponent(requestId)}/appointments`, { method: 'POST', body: JSON.stringify({ profile_id: profileId, starts_at: button.dataset.slot }) });
        closeModals();
        showToast(`Meeting booked for ${formatWhen(button.dataset.slot)}.`, 'success');
        renderRequestDetail(detail);
        loadRequests({ silent: true });
      } catch (error) {
        setButtonLoading(button, false);
        showToast(error.message, 'error');
      }
    }));
  } catch (error) {
    body.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

function renderRequestExtras(detail) {
  const open = !['completed', 'cancelled'].includes(detail.status);
  const assignBox = document.querySelector('#request-assign');
  const acting = actingAs();
  const actingCompany = acting.type === 'company' ? identities?.companies.find((company) => company.organization_id === acting.id) : null;
  if (detail.can_assign) {
    assignBox.innerHTML = `<span class="section-tag">Handled by</span><div style="display:flex;gap:6px;margin:6px 0 18px"><select id="assign-select" aria-label="Assign to" style="flex:1;min-width:0;min-height:36px;padding:0 8px;border:1px solid var(--line);border-radius:7px;font:inherit"><option value="">Unassigned</option>${detail.assignable_members.map((member) => `<option value="${escapeHtml(member.user_id)}" ${member.user_id === detail.assigned_user_id ? 'selected' : ''}>${escapeHtml(member.full_name)}${member.member_role === 'admin' ? ' (admin)' : ''}</option>`).join('')}</select><button class="secondary" type="button" id="assign-save">Assign</button></div>`;
    document.querySelector('#assign-save').addEventListener('click', async (event) => {
      const button = event.currentTarget;
      setButtonLoading(button, true, '…');
      try {
        const updated = await api(`/requests/${encodeURIComponent(detail.id)}/assign`, { method: 'POST', body: JSON.stringify({ user_id: document.querySelector('#assign-select').value || null }) });
        showToast('Assignment saved.', 'success');
        renderRequestDetail(updated);
        loadRequests({ silent: true });
      } catch (error) {
        setButtonLoading(button, false);
        showToast(error.message, 'error');
      }
    });
  } else if (detail.my_role === 'company' && actingCompany?.member_role === 'admin' && !actingCompany.plan_active) {
    assignBox.innerHTML = '<p class="muted" style="margin:0 0 16px">🔒 Assign requests to your team with <a href="plans.html">Enterprise</a>.</p>';
  } else {
    assignBox.innerHTML = '';
  }

  const meetingsBox = document.querySelector('#request-meetings');
  if (!detail.appointments.length && !detail.bookable_profiles.length) { meetingsBox.innerHTML = ''; return; }
  meetingsBox.innerHTML = `<span class="section-tag">Meetings</span>
    ${detail.appointments.map((meeting) => {
      const active = ACTIVE_MEETING.includes(meeting.status);
      return `<div class="meeting" style="margin:6px 0;${active ? '' : 'opacity:.6'}"><strong>${active ? '' : '<s>'}${escapeHtml(formatWhen(meeting.starts_at))}${active ? '' : '</s>'}</strong><span>${escapeHtml(meeting.with_name)} · 30 min · ${meeting.status}</span>${active && open ? `<button class="secondary" type="button" data-cancel-meeting="${escapeHtml(meeting.id)}" style="min-height:28px;margin-top:6px;font-size:11px">Cancel meeting</button>` : ''}</div>`;
    }).join('')}
    ${detail.bookable_profiles.map((target) => `<button class="primary" type="button" data-book-profile="${escapeHtml(target.profile_id)}" data-book-name="${escapeHtml(target.name)}" style="width:100%;margin-top:6px">📅 Book a time${detail.bookable_profiles.length > 1 ? ` · ${escapeHtml(target.name)}` : ''}</button>`).join('')}
    <div style="height:18px"></div>`;
  meetingsBox.querySelectorAll('[data-book-profile]').forEach((button) => button.addEventListener('click', () => openBooking(detail.id, button.dataset.bookProfile, button.dataset.bookName)));
  meetingsBox.querySelectorAll('[data-cancel-meeting]').forEach((button) => button.addEventListener('click', async () => {
    if (!confirm('Cancel this meeting?')) return;
    setButtonLoading(button, true, 'Cancelling…');
    try {
      renderRequestDetail(await api(`/requests/${encodeURIComponent(detail.id)}/appointments/${encodeURIComponent(button.dataset.cancelMeeting)}/cancel`, { method: 'POST' }));
      showToast('Meeting cancelled.', 'success');
      loadRequests({ silent: true });
    } catch (error) {
      setButtonLoading(button, false);
      showToast(error.message, 'error');
    }
  }));
}

/* ---------- Public profile extras ---------- */

// Host suffix -> [label, icon text, brand colour]; mirrors backend app/core/links.py.
const LINK_PLATFORMS = [
  ['instagram.com', 'Instagram', 'IG', '#d6249f'], ['youtube.com', 'YouTube', '▶', '#ff0000'], ['youtu.be', 'YouTube', '▶', '#ff0000'],
  ['linkedin.com', 'LinkedIn', 'in', '#0a66c2'], ['facebook.com', 'Facebook', 'f', '#1877f2'], ['fb.com', 'Facebook', 'f', '#1877f2'],
  ['x.com', 'X', 'X', '#111111'], ['twitter.com', 'X', 'X', '#111111'], ['github.com', 'GitHub', 'GH', '#24292f'],
  ['wa.me', 'WhatsApp', '✆', '#25d366'], ['whatsapp.com', 'WhatsApp', '✆', '#25d366'], ['t.me', 'Telegram', '✈', '#229ed9'],
  ['behance.net', 'Behance', 'Bē', '#1769ff'], ['dribbble.com', 'Dribbble', '●', '#ea4c89'], ['medium.com', 'Medium', 'M', '#000000'],
  ['threads.net', 'Threads', '@', '#000000'], ['pinterest.com', 'Pinterest', 'P', '#e60023'],
];

function linkInfo(url) {
  let host = '';
  let path = '';
  try {
    const parsed = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(url) ? url : `https://${url}`);
    host = parsed.hostname.toLowerCase();
    path = parsed.pathname.replace(/\/$/, '');
  } catch (_) { /* not a link yet */ }
  const match = LINK_PLATFORMS.find(([suffix]) => host === suffix || host.endsWith(`.${suffix}`));
  return { name: match ? match[1] : 'Website', glyph: match ? match[2] : '🌐', color: match ? match[3] : '#5b6b85', host: host.replace(/^www\./, ''), display: host.replace(/^www\./, '') + path };
}

function linkIcon(url) {
  const info = linkInfo(url);
  return `<span class="link-icon" style="background:${info.color}">${info.glyph}</span>`;
}

function linkChip(label, url) {
  const info = linkInfo(url);
  return `<a class="link-chip" href="${safeHref(url)}" target="_blank" rel="noopener noreferrer">${linkIcon(url)}${escapeHtml(label || info.name)}<small>${escapeHtml(info.display)}</small></a>`;
}

function monthYear(isoDate) {
  const [year, month] = isoDate.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
}

function spanText(start, end) {
  const [startYear, startMonth] = start.split('-').map(Number);
  const now = new Date();
  const [endYear, endMonth] = end ? end.split('-').map(Number) : [now.getFullYear(), now.getMonth() + 1];
  const total = Math.max(1, (endYear - startYear) * 12 + (endMonth - startMonth) + 1);
  const years = Math.floor(total / 12);
  const months = total % 12;
  return [years ? `${years} yr${years > 1 ? 's' : ''}` : '', months ? `${months} mo${months > 1 ? 's' : ''}` : ''].filter(Boolean).join(' ');
}

function sectionCard(title, body, editKey, own) {
  return `<article class="content-card"><div class="card-head"><h2>${title}</h2>${own ? `<button class="secondary card-edit" type="button" data-edit-section="${editKey}">✎ Edit</button>` : ''}</div><div style="margin-top:10px">${body}</div></article>`;
}

function renderProfileExtras(profile, own = false) {
  document.querySelector('#profile-bookable').hidden = !profile.bookable;
  const cards = [];
  const prompt = (key, text) => `<button type="button" class="add-prompt" data-edit-section="${key}">${text}</button>`;
  const experiences = profile.experiences || [];
  const educations = profile.educations || [];
  if (profile.kind === 'expert' && (experiences.length || own)) {
    cards.push(sectionCard('Experience', experiences.length
      ? experiences.map((xp) => `<div class="xp-item"><div class="xp-logo">${escapeHtml(initialsOf(xp.organization))}</div><div><strong>${escapeHtml(xp.title)}</strong><span>${escapeHtml(xp.organization)}${xp.location ? ` · ${escapeHtml(xp.location)}` : ''}</span><span class="muted">${monthYear(xp.start_date)} – ${xp.end_date ? monthYear(xp.end_date) : 'Present'} · ${spanText(xp.start_date, xp.end_date)}</span>${xp.description ? `<p>${escapeHtml(xp.description)}</p>` : ''}</div></div>`).join('')
      : prompt('experience', '+ Add your work experience'), 'experience', own));
  }
  if (profile.kind === 'expert' && (educations.length || own)) {
    cards.push(sectionCard('Education', educations.length
      ? educations.map((edu) => `<div class="xp-item"><div class="xp-logo">🎓</div><div><strong>${escapeHtml(edu.school)}</strong>${edu.degree || edu.field_of_study ? `<span>${escapeHtml([edu.degree, edu.field_of_study].filter(Boolean).join(', '))}</span>` : ''}${edu.start_year || edu.end_year ? `<span class="muted">${[edu.start_year, edu.end_year].filter(Boolean).join(' – ')}</span>` : ''}${edu.description ? `<p>${escapeHtml(edu.description)}</p>` : ''}</div></div>`).join('')
      : prompt('education', '+ Add your education'), 'education', own));
  }
  if (profile.credentials?.length || own) {
    cards.push(sectionCard('Licences & certifications', profile.credentials?.length
      ? profile.credentials.map((credential) => `<div class="offering"><div><strong>${escapeHtml(credential.title)}</strong>${credential.issuing_body ? `<span class="muted">${escapeHtml(credential.issuing_body)}</span>` : ''}</div><span class="${credential.verified ? 'verified' : 'muted'}">${credential.verified ? '● Verified' : 'Pending check'}</span></div>`).join('')
      : prompt('credentials', '+ Add a licence or certificate'), 'credentials', own));
  }
  const links = [
    profile.intro_video_url ? { label: 'Intro video', url: profile.intro_video_url } : null,
    profile.portfolio_url ? { label: 'Portfolio', url: profile.portfolio_url } : null,
    ...(profile.social_links || []).map((link) => ({ label: link.platform, url: link.url })),
  ].filter(Boolean);
  if (links.length || own) {
    cards.push(sectionCard('Links', links.length
      ? `<div class="link-list">${links.map((link) => linkChip(link.label, link.url)).join('')}</div>`
      : prompt('links', '+ Add Instagram, YouTube, LinkedIn or your website'), 'links', own));
  }
  if (profile.offerings?.length) {
    cards.push(`<article class="content-card"><h2>Services &amp; prices</h2>${profile.offerings.map((offering) => `<div class="offering"><div><strong>${escapeHtml(offering.title)}</strong>${offering.description ? `<span class="muted">${escapeHtml(offering.description)}</span>` : ''}</div><span class="price-tag">${formatPrice(offering.price_min_inr, offering.price_max_inr)}</span></div>`).join('')}</article>`);
  }
  const box = document.querySelector('#profile-extras');
  box.innerHTML = cards.join('');
  box.querySelectorAll('[data-edit-section]').forEach((button) => button.addEventListener('click', () => openProfileEditor(profile.id, button.dataset.editSection)));
}

/* ---------- My profile & customer profiles ---------- */

function openMyProfile() {
  if (!accessToken) { window.location.href = 'auth.html'; return; }
  const acting = actingAs();
  if (acting.type === 'expert' && identities?.expert_profile) { openProfile(identities.expert_profile.id); return; }
  if (acting.type === 'company') {
    const company = identities?.companies.find((item) => item.organization_id === acting.id);
    if (company?.profile_id) { openProfile(company.profile_id); return; }
  }
  showView('me');
  renderMe();
}

function customerCard(data, own) {
  const since = new Date(data.member_since).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  const portrait = data.avatar_url ? `<img src="${safeHref(data.avatar_url)}" alt="">` : escapeHtml(initialsOf(data.full_name));
  return `<article class="profile-hero"><div class="profile-summary"><div class="portrait">${portrait}</div><div>
      <span class="section-tag">Customer</span><h1>${escapeHtml(data.full_name)}</h1>
      <p>${[data.city, `Member since ${since}`].filter(Boolean).map(escapeHtml).join(' · ')}</p>
      <div class="tags">${(data.interests || []).map((interest) => `<span class="tag">${escapeHtml(interest)}</span>`).join('')}</div>
      ${own ? '<div class="profile-owner-actions"><button class="primary" type="button" id="me-edit">✎ Edit profile</button></div>' : ''}
    </div></div>
    <div class="trust-bar" style="grid-template-columns:1fr"><div class="trust-item"><small>Requests completed</small><strong>${data.completed_requests}</strong></div></div></article>
    <article class="content-card"><h2>About</h2>${data.bio
      ? `<p style="white-space:pre-wrap">${escapeHtml(data.bio)}</p>`
      : (own ? '<button type="button" class="add-prompt" id="me-add-bio">+ Add a short about – helps experts understand what you need</button>' : '<p class="muted" style="margin:0">Nothing here yet.</p>')}</article>`;
}

function renderMe() {
  const body = document.querySelector('#me-body');
  if (!currentUser) { body.innerHTML = '<p class="muted">Sign in to see your profile.</p>'; return; }
  const completed = requestsCache.filter((request) => request.my_role === 'customer' && request.status === 'completed').length;
  body.innerHTML = `<div style="max-width:760px">${customerCard({ ...currentUser, completed_requests: completed }, true)}</div>`;
  document.querySelector('#me-edit').addEventListener('click', renderMeEditor);
  document.querySelector('#me-add-bio')?.addEventListener('click', renderMeEditor);
}

function renderMeEditor() {
  const user = currentUser;
  document.querySelector('#me-body').innerHTML = `<form id="me-form" class="content-card" style="max-width:760px;margin-top:0">
      <h2>Edit profile</h2>
      <div class="editor-grid">
        ${field('me-name', 'Name', user.full_name, 'required minlength="2" maxlength="120"')}
        ${field('me-city', 'City', user.city, 'maxlength="100"')}
        <div class="field" style="grid-column:1/-1"><label for="me-avatar">Photo link</label><input id="me-avatar" value="${escapeHtml(user.avatar_url ?? '')}" maxlength="500" placeholder="Paste an image link"></div>
      </div>
      <div class="field"><label for="me-bio">About you</label><textarea id="me-bio" rows="4" maxlength="1000" placeholder="e.g. Small business owner in Chennai, looking for help with taxes and insurance.">${escapeHtml(user.bio ?? '')}</textarea></div>
      <p class="muted" style="margin:0 0 10px">Only experts and companies you send a request to can see this.</p>
      <div class="modal-actions"><button class="secondary" type="button" id="me-cancel">Cancel</button><button class="primary" type="submit" id="me-save">Save</button></div>
    </form>`;
  document.querySelector('#me-cancel').addEventListener('click', renderMe);
  document.querySelector('#me-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = document.querySelector('#me-save');
    const value = (id) => document.querySelector(id).value.trim();
    setButtonLoading(button, true, 'Saving…');
    try {
      const updated = await api('/auth/me', { method: 'PATCH', body: JSON.stringify({ full_name: value('#me-name'), city: value('#me-city') || null, avatar_url: value('#me-avatar') || null, bio: value('#me-bio') || null }) });
      applySignedInUser(updated);
      renderMe();
      showToast('Profile saved.', 'success');
    } catch (error) {
      setButtonLoading(button, false);
      showToast(error.message, 'error');
    }
  });
}

async function openCustomerProfile(requestId) {
  const body = document.querySelector('#customer-body');
  body.innerHTML = '<p class="muted"><span class="spinner"></span>Loading…</p>';
  openModal('customer-modal');
  try {
    body.innerHTML = customerCard(await api(`/requests/${encodeURIComponent(requestId)}/customer`), false);
  } catch (error) {
    body.innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

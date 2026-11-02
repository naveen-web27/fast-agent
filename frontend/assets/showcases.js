// Uses the marketplace's API, profile, authentication, and modal helpers.
(() => {
  const styles = document.createElement('style');
  styles.textContent = `
    .showcase-discover { margin:0 0 24px; padding:18px; border:1px solid var(--line); border-radius:12px; background:#fff; }
    .showcase-heading { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:14px; }
    .showcase-heading h2 { margin:0 0 4px; font-size:18px; }
    .showcase-heading p { max-width:650px; margin:0; font-size:12px; }
    .showcase-strip { display:flex; gap:14px; overflow-x:auto; padding:2px 2px 14px; scroll-snap-type:x proximity; }
    .showcase-card { min-width:0; overflow:hidden; border:1px solid var(--line); border-radius:12px; background:#fff; }
    .showcase-strip .showcase-card { flex:0 0 228px; scroll-snap-align:start; }
    .showcase-cover { position:relative; display:grid; place-items:center; aspect-ratio:3/4; overflow:hidden; color:#fff; background:var(--navy); text-decoration:none; }
    .showcase-cover img { width:100%; height:100%; min-height:0; object-fit:contain; }
    .showcase-cover span { position:absolute; right:10px; bottom:10px; padding:6px 9px; border-radius:6px; background:#101b31e6; font-size:11px; font-weight:800; }
    .showcase-cover .showcase-image-missing { position:static; padding:20px; text-align:center; }
    .showcase-copy { padding:14px; }
    .showcase-copy h3 { margin:6px 0; font-size:14px; overflow-wrap:anywhere; }
    .showcase-copy p { margin:0 0 10px; color:var(--muted); font-size:12px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .showcase-copy .showcase-platform { color:var(--teal); font-size:11px; font-weight:800; }
    .showcase-copy .showcase-description { display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
    .showcase-actions { display:flex; flex-wrap:wrap; gap:7px; margin-top:10px; }
    .showcase-actions .secondary { min-height:34px; padding:6px 9px; font-size:11px; }
    .showcase-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:18px; }
    .showcase-grid > .muted { grid-column:1/-1; }
    .showcase-preview { display:grid; place-items:center; min-height:140px; max-height:320px; margin:12px 0; overflow:hidden; border:1px dashed var(--line); border-radius:10px; background:#f4f6fa; }
    .showcase-preview img { display:block; max-width:100%; max-height:300px; object-fit:contain; }
    .showcase-form { display:grid; gap:12px; margin-top:18px; }
    .showcase-manager-list { display:grid; gap:8px; margin-top:12px; }
    .showcase-manager-row { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; padding:10px 0; border-top:1px solid var(--line); }
    .showcase-manager-row strong { overflow-wrap:anywhere; }
    .showcase-error { color:#b4233f; font-size:13px; white-space:pre-wrap; }
    .showcase-error:empty { display:none; }
    .showcase-form label { font-weight:700; font-size:12px; }
    .showcase-form select { width:100%; min-height:42px; }
    @media (max-width:720px) { .showcase-discover { padding:12px; } .showcase-strip .showcase-card { flex-basis:210px; } .showcase-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; } .showcase-copy { padding:10px; } .showcase-copy h3 { font-size:13px; } }
    @media (max-width:360px) { .showcase-grid { grid-template-columns:1fr; } }
    @media print { .showcase-discover,#profile-showcases { display:none; } }
  `;
  document.head.append(styles);

  let page = 1;
  let stripRequest = 0;
  let feedRequest = 0;
  let managerRequest = 0;
  let profileRequest = 0;
  let managedProfileId = null;
  let managed = null;
  let editingId = null;
  let checkedSource = null;
  let coverUrl = null;
  let coverFile = null;
  let objectUrl = null;
  let previewRequest = 0;

  function platformName(platform) { return platform === 'youtube' ? 'YouTube' : 'Instagram'; }

  function card(item) {
    const article = document.createElement('article');
    article.className = 'showcase-card';
    const provider = platformName(item.platform);
    article.innerHTML = `
      <a class="showcase-cover" href="${safeHref(item.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHtml(`Watch ${item.title} on ${provider}`)}">
        <img src="${safeHref(item.cover_url)}" alt="${escapeHtml(item.title)}" loading="lazy" referrerpolicy="no-referrer">
        <span>Watch on ${provider} &#8599;</span>
      </a>
      <div class="showcase-copy">
        <span class="showcase-platform">${provider} &middot; Provider showcase</span>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="showcase-description">${escapeHtml(item.description)}</p>
        <button class="secondary showcase-profile" type="button">${escapeHtml(item.provider_name)}</button>
        <div class="showcase-actions"><button class="secondary showcase-report" type="button">Report</button></div>
      </div>`;
    article.querySelector('img').addEventListener('error', (event) => {
      event.target.remove();
      const placeholder = document.createElement('strong');
      placeholder.className = 'showcase-image-missing';
      placeholder.textContent = 'Preview unavailable. Watch on the original platform.';
      article.querySelector('.showcase-cover').prepend(placeholder);
    }, { once: true });
    article.querySelector('.showcase-profile').addEventListener('click', () => openProfile(item.profile_id));
    article.querySelector('.showcase-report').addEventListener('click', () => {
      document.querySelector('#support-whatsapp').href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(`Please review video showcase ${item.id}: ${item.source_url}`)}`;
      document.querySelector('#support-email').href = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent('Report video showcase')}&body=${encodeURIComponent(`Showcase: ${item.id}\nProfile: ${item.profile_id}\nVideo: ${item.source_url}\nReason: `)}`;
      openModal('support-modal');
    });
    return article;
  }

  function renderCards(root, items, empty) {
    root.replaceChildren();
    if (!items.length) {
      const note = document.createElement('p');
      note.className = 'muted';
      note.textContent = empty;
      root.append(note);
    } else items.forEach((item) => root.append(card(item)));
  }

  function loadError(root, message, retry) {
    root.replaceChildren();
    const note = document.createElement('p');
    note.className = 'muted';
    note.textContent = message;
    const button = document.createElement('button');
    button.className = 'secondary';
    button.type = 'button';
    button.textContent = 'Retry';
    button.addEventListener('click', retry);
    root.append(note, button);
  }

  async function loadStrip() {
    const ticket = ++stripRequest;
    const root = document.querySelector('#showcase-strip');
    try {
      const data = await api('/showcases?page_size=8');
      if (ticket !== stripRequest) return;
      renderCards(root, data.results, 'No video showcases yet. Experts and companies can add theirs from View all showcases.');
    } catch (error) {
      if (ticket !== stripRequest) return;
      loadError(root, `Could not load video showcases. ${error.message}`, loadStrip);
    }
  }

  window.loadVideoShowcases = async () => {
    const ticket = ++feedRequest;
    const root = document.querySelector('#showcase-results');
    document.querySelector('#showcase-pagination').hidden = true;
    root.innerHTML = '<p class="muted">Loading showcases...</p>';
    try {
      const data = await api(`/showcases?page=${page}&page_size=12`);
      if (ticket !== feedRequest) return;
      if (!data.results.length && page > 1) { page -= 1; return window.loadVideoShowcases(); }
      renderCards(root, data.results, 'No video showcases yet. Be the first provider to share your work.');
      document.querySelector('#showcase-pagination').hidden = data.total <= 12;
      document.querySelector('#showcase-page').textContent = `Page ${page} of ${Math.max(1, Math.ceil(data.total / 12))}`;
      document.querySelector('#showcase-prev').disabled = page <= 1;
      document.querySelector('#showcase-next').disabled = page * 12 >= data.total;
    } catch (error) {
      if (ticket !== feedRequest) return;
      loadError(root, `Could not load showcases. ${error.message}`, window.loadVideoShowcases);
    }
  };
  document.querySelector('#showcase-prev').addEventListener('click', () => { if (page > 1) { page -= 1; window.loadVideoShowcases(); } });
  document.querySelector('#showcase-next').addEventListener('click', () => { page += 1; window.loadVideoShowcases(); });

  const profileBox = document.createElement('article');
  profileBox.id = 'profile-showcases';
  profileBox.className = 'content-card';
  document.querySelector('#profile-extras').after(profileBox);
  window.loadProfileShowcases = async (id, own) => {
    const ticket = ++profileRequest;
    profileBox.innerHTML = '<h2>Video showcases</h2><p class="muted">Loading showcases...</p>';
    try {
      const data = await api(`/showcases?profile_id=${encodeURIComponent(id)}&page_size=30`);
      if (ticket !== profileRequest || currentProfileId !== id) return;
      profileBox.innerHTML = '<h2>Video showcases</h2><p class="muted">External provider-posted videos, not an endorsement.</p><div class="showcase-strip"></div>';
      renderCards(profileBox.querySelector('.showcase-strip'), data.results, 'No video showcases published.');
      if (own) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'secondary';
        button.textContent = 'Manage video showcases';
        button.addEventListener('click', () => window.openShowcaseManager(id));
        profileBox.append(button);
      }
    } catch (error) {
      if (ticket === profileRequest && currentProfileId === id) loadError(profileBox, error.message, () => window.loadProfileShowcases(id, own));
    }
  };

  const modal = document.createElement('div');
  modal.id = 'showcase-manager';
  modal.className = 'modal wide';
  modal.hidden = true;
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-labelledby', 'showcase-manager-title');
  modal.innerHTML = `
    <button class="modal-x" type="button" id="showcase-close" aria-label="Close showcase manager">&#215;</button>
    <h2 id="showcase-manager-title">Manage video showcases</h2>
    <p class="modal-note">2 posts per profile on Free; 10 with that profile's active Pro or Enterprise plan. Videos remain on YouTube or Instagram.</p>
    <label for="showcase-profile">Publish as</label><select id="showcase-profile"></select>
    <p id="showcase-quota" class="muted" role="status"></p>
    <p id="showcase-error" class="showcase-error" role="alert"></p>
    <div id="showcase-owned" class="showcase-manager-list"></div>
    <form id="showcase-form" class="showcase-form">
      <div class="field"><label for="showcase-source">YouTube Shorts or Instagram Reel link</label><input id="showcase-source" required maxlength="500" placeholder="https://www.youtube.com/shorts/..." autocomplete="off"></div>
      <button class="secondary" type="button" id="showcase-check">Load preview</button>
      <p class="muted" id="showcase-preview-message" role="status">Paste a video link and load its preview first.</p>
      <div class="showcase-preview" id="showcase-cover-preview">Your cover preview appears here.</div>
      <div class="field"><label for="showcase-cover-file">Upload your thumbnail or poster</label><input id="showcase-cover-file" type="file" accept="image/jpeg,image/png,image/webp"><small class="muted">Required if an automatic thumbnail is unavailable. JPG, PNG or WebP up to 8 MB; optimized before upload. The full image is shown without cropping. Only upload images you own or may use.</small></div>
      <div class="field"><label for="showcase-title">Title</label><input id="showcase-title" required minlength="2" maxlength="120"></div>
      <div class="field"><label for="showcase-description">Short description</label><textarea id="showcase-description" required minlength="2" maxlength="600" rows="3"></textarea></div>
      <p class="muted">Only link videos you own or are authorized to promote. Do not post misleading claims or private customer information.</p>
      <div class="modal-actions"><button class="secondary" type="button" id="showcase-cancel">New post / cancel edit</button><button class="primary" type="submit" id="showcase-publish">Publish showcase</button></div>
    </form>`;
  document.body.append(modal);
  const form = document.querySelector('#showcase-form');
  const errorBox = document.querySelector('#showcase-error');
  const previewBox = document.querySelector('#showcase-cover-preview');
  const sourceInput = document.querySelector('#showcase-source');
  const fileInput = document.querySelector('#showcase-cover-file');
  const profileSelect = document.querySelector('#showcase-profile');

  function clearCover() {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null;
    coverUrl = null;
    coverFile = null;
    fileInput.value = '';
    previewBox.textContent = 'Your cover preview appears here.';
  }

  function showCover(url, isUpload = false) {
    previewBox.replaceChildren();
    const image = document.createElement('img');
    image.alt = 'Showcase cover preview';
    image.referrerPolicy = 'no-referrer';
    const unavailable = () => {
      if (previewBox.firstChild !== image) return;
      coverUrl = null;
      if (isUpload) coverFile = null;
      previewBox.textContent = 'Preview unavailable. Upload a thumbnail or poster to continue.';
      document.querySelector('#showcase-preview-message').textContent = 'We could not load this cover. Upload your own thumbnail or poster.';
    };
    image.addEventListener('error', unavailable, { once: true });
    image.addEventListener('load', () => {
      // YouTube can return a tiny placeholder with HTTP 200 for an unavailable video.
      if (!isUpload && url.startsWith('https://i.ytimg.com/') && image.naturalWidth <= 120 && image.naturalHeight <= 90) unavailable();
    }, { once: true });
    image.src = url;
    previewBox.append(image);
  }

  function resetForm() {
    ++previewRequest;
    editingId = null;
    checkedSource = null;
    form.reset();
    clearCover();
    errorBox.textContent = '';
    document.querySelector('#showcase-preview-message').textContent = 'Paste a video link and load its preview first.';
    document.querySelector('#showcase-publish').textContent = 'Publish showcase';
    form.hidden = Boolean(managed && managed.total >= managed.limit);
  }

  async function refreshManager() {
    const ticket = ++managerRequest;
    managed = null;
    form.hidden = true;
    document.querySelector('#showcase-owned').textContent = 'Loading your posts...';
    document.querySelector('#showcase-quota').textContent = '';
    errorBox.textContent = '';
    try {
      const data = await api(`/profiles/${managedProfileId}/showcases/manage`);
      if (ticket !== managerRequest) return;
      managed = data;
      document.querySelector('#showcase-quota').textContent = `${data.total}/${data.limit} showcases used. ${data.plan_active ? 'Paid plan active.' : 'Free plan. Upgrade this profile for up to 10.'}${data.total > data.limit ? ' Existing posts remain published after plan expiry; remove posts to add another.' : ''}`;
      if (!data.plan_active) {
        const upgrade = document.createElement('a');
        upgrade.href = 'plans.html';
        upgrade.textContent = ' View plans';
        document.querySelector('#showcase-quota').append(upgrade);
      }
      const list = document.querySelector('#showcase-owned');
      list.replaceChildren();
      for (const item of data.results) {
        const row = document.createElement('div');
        row.className = 'showcase-manager-row';
        row.innerHTML = `<strong>${escapeHtml(item.title)}</strong><div class="showcase-actions"><button class="secondary" type="button" data-edit>Edit</button><button class="secondary" type="button" data-remove>Remove</button></div>`;
        row.querySelector('[data-edit]').addEventListener('click', () => {
          resetForm();
          editingId = item.id;
          checkedSource = item.source_url;
          coverUrl = item.cover_url;
          sourceInput.value = item.source_url;
          document.querySelector('#showcase-title').value = item.title;
          document.querySelector('#showcase-description').value = item.description;
          document.querySelector('#showcase-publish').textContent = 'Save changes';
          document.querySelector('#showcase-preview-message').textContent = `Published ${platformName(item.platform)} video. You can change the cover or details.`;
          showCover(coverUrl);
          form.hidden = false;
        });
        row.querySelector('[data-remove]').addEventListener('click', async (event) => {
          if (!confirm('Remove this showcase from RightConnect? The original video will not be deleted.')) return;
          const button = event.currentTarget;
          setButtonLoading(button, true, 'Removing...');
          try {
            await api(`/profiles/${managedProfileId}/showcases/${item.id}`, { method: 'DELETE' });
            await refreshManager();
            refreshPublicViews();
            showToast('Showcase removed.', 'success');
          } catch (error) { errorBox.textContent = error.message; }
          finally { setButtonLoading(button, false); }
        });
        list.append(row);
      }
      resetForm();
    } catch (error) {
      if (ticket !== managerRequest) return;
      document.querySelector('#showcase-owned').textContent = '';
      errorBox.textContent = `Could not load your showcases. ${error.message} Close and reopen to retry.`;
    }
  }

  window.openShowcaseManager = async (requestedProfileId) => {
    if (!accessToken) { location.href = 'auth.html#sign-in'; return; }
    if (!identities) await loadIdentities();
    const profiles = [];
    if (identities?.expert_profile) profiles.push({ id: identities.expert_profile.id, name: 'Expert profile' });
    for (const company of identities?.companies || []) {
      if (company.member_role === 'admin' && company.profile_id) profiles.push({ id: company.profile_id, name: company.name });
    }
    if (!profiles.length) {
      showToast(identities ? 'Add an expert or company profile from the workspace menu before publishing.' : 'Could not load your profiles. Please try again.', 'error');
      return;
    }
    closeModals();
    profileSelect.replaceChildren();
    profiles.forEach((profile) => {
      const option = document.createElement('option');
      option.value = profile.id;
      option.textContent = profile.name;
      profileSelect.append(option);
    });
    managedProfileId = profiles.some((profile) => profile.id === requestedProfileId) ? requestedProfileId : profiles[0].id;
    profileSelect.value = managedProfileId;
    openModal('showcase-manager');
    document.querySelector('#showcase-close').focus();
    await refreshManager();
  };
  document.querySelector('#showcase-manage').addEventListener('click', () => window.openShowcaseManager());
  document.querySelector('#showcase-close').addEventListener('click', () => { ++previewRequest; clearCover(); closeModals(); });
  profileSelect.addEventListener('change', () => { managedProfileId = profileSelect.value; resetForm(); refreshManager(); });
  document.querySelector('#showcase-cancel').addEventListener('click', resetForm);
  sourceInput.addEventListener('input', () => {
    ++previewRequest;
    checkedSource = null;
    clearCover();
    document.querySelector('#showcase-preview-message').textContent = 'Link changed. Load its preview before publishing.';
  });
  document.querySelector('#showcase-check').addEventListener('click', async (event) => {
    const button = event.currentTarget;
    const source = sourceInput.value.trim();
    const ticket = ++previewRequest;
    checkedSource = null;
    clearCover();
    errorBox.textContent = '';
    setButtonLoading(button, true, 'Checking...');
    try {
      const data = await api('/showcases/preview', { method: 'POST', body: JSON.stringify({ source_url: source }) });
      if (ticket !== previewRequest) return;
      checkedSource = data.source_url;
      sourceInput.value = checkedSource;
      document.querySelector('#showcase-preview-message').textContent = data.message;
      if (data.thumbnail_url) { coverUrl = data.thumbnail_url; showCover(coverUrl); }
      else previewBox.textContent = 'Upload your thumbnail or poster to continue.';
    } catch (error) { if (ticket === previewRequest) errorBox.textContent = error.message; }
    finally { setButtonLoading(button, false); }
  });
  fileInput.addEventListener('change', () => {
    errorBox.textContent = '';
    if (!checkedSource) {
      fileInput.value = '';
      errorBox.textContent = 'Load a valid video link before selecting a cover.';
      return;
    }
    const file = fileInput.files[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 8 * 1024 * 1024) {
      fileInput.value = '';
      errorBox.textContent = 'Choose a JPG, PNG, or WebP image up to 8 MB.';
      return;
    }
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    coverUrl = null;
    coverFile = file;
    objectUrl = URL.createObjectURL(file);
    showCover(objectUrl, true);
  });

  function refreshPublicViews() {
    loadStrip();
    if (document.querySelector('#showcases').classList.contains('active')) window.loadVideoShowcases();
    if (currentProfileId && document.querySelector('#profile').classList.contains('active')) window.loadProfileShowcases(currentProfileId, ownsProfile(currentProfileId));
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.textContent = '';
    if (!checkedSource || checkedSource !== sourceInput.value.trim()) { errorBox.textContent = 'Load the video preview first.'; return; }
    if (!coverUrl && !coverFile) { errorBox.textContent = 'Upload a thumbnail or poster before publishing.'; return; }
    const image = previewBox.querySelector('img');
    if (!image?.complete || !image.naturalWidth) { errorBox.textContent = 'Wait for the cover to load, or upload another image.'; return; }
    const button = document.querySelector('#showcase-publish');
    const id = managedProfileId;
    const postId = editingId;
    const payload = {
      source_url: checkedSource,
      title: document.querySelector('#showcase-title').value.trim(),
      description: document.querySelector('#showcase-description').value.trim(),
      cover_url: coverUrl,
    };
    const file = coverFile;
    profileSelect.disabled = true;
    form.querySelectorAll('input, textarea, button').forEach((input) => { input.disabled = true; });
    setButtonLoading(button, true, file ? 'Uploading...' : 'Saving...');
    try {
      if (file) payload.cover_url = await window.uploadProfileImage(file, `showcase-${crypto.randomUUID()}`);
      await api(`/profiles/${id}/showcases${postId ? `/${postId}` : ''}`, { method: postId ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      await refreshManager();
      refreshPublicViews();
      showToast(postId ? 'Showcase updated.' : 'Showcase published.', 'success');
    } catch (error) { errorBox.textContent = error.message; }
    finally {
      profileSelect.disabled = false;
      form.querySelectorAll('input, textarea, button').forEach((input) => { input.disabled = false; });
      setButtonLoading(button, false);
      button.textContent = editingId ? 'Save changes' : 'Publish showcase';
    }
  });
  loadStrip();
  if (document.querySelector('#showcases').classList.contains('active')) window.loadVideoShowcases();
  if (currentProfileId && document.querySelector('#profile').classList.contains('active')) window.loadProfileShowcases(currentProfileId, ownsProfile(currentProfileId));
})();

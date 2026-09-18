/* ============================================================
   TaskFlow — Frontend Application Logic
   Communicates with the FastAPI backend at /tasks and /employees
   ============================================================ */

'use strict';

// The frontend is served from the same FastAPI origin, so relative URLs work.
const API = '';

// ── State ──────────────────────────────────────────────────
let allTasks = [];
let employees = [];
let sortKey = 'created_at';
let sortAsc = false;
let activeStatusFilter = '';
let taskToDelete = null;

// ── Avatar helpers ─────────────────────────────────────────
const AVATAR_CLASSES = {
  Arun: 'av-arun',
  Priya: 'av-priya',
  Karthik: 'av-karthik',
  Rahul: 'av-rahul',
  Sneha: 'av-sneha',
};

function getInitials(name) {
  if (!name) return '?';
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function avatarHtml(name) {
  if (!name) return '';
  const cls = AVATAR_CLASSES[name] || 'av-default';
  return `<span class="avatar ${cls}">${getInitials(name)}</span>`;
}

// ── Status helpers ─────────────────────────────────────────
function statusBadgeHtml(status) {
  const map = {
    'To Do':       ['badge-todo',   'To Do'],
    'In Progress': ['badge-inprog', 'In Progress'],
    'Done':        ['badge-done',   'Done'],
  };
  const [cls, label] = map[status] || ['badge-todo', status || 'To Do'];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Priority helpers ───────────────────────────────────────
function priorityHtml(priority) {
  const map = {
    'Low':    'prio-low',
    'Medium': 'prio-med',
    'High':   'prio-high',
  };
  const cls = map[priority] || 'prio-med';
  return `<span class="${cls}"><span class="prio-dot">${priority || 'Medium'}</span></span>`;
}

// ── Date formatting ────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── Toast notifications ────────────────────────────────────
function showToast(message, type = 'info') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ── API helpers ────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// ── Load employees ─────────────────────────────────────────
async function loadEmployees() {
  try {
    employees = await apiFetch('/employees');

    // Populate sidebar team list
    const sidebarTeam = document.getElementById('sidebar-team');
    sidebarTeam.innerHTML = employees.map(e => `
      <div class="team-member">
        ${avatarHtml(e.name)}
        <span>${e.name}</span>
      </div>
    `).join('');

    // Populate assignee dropdowns
    const assigneeOptions = employees.map(e =>
      `<option value="${e.name}">${e.name}</option>`
    ).join('');

    document.getElementById('field-assignee').innerHTML =
      '<option value="">— Unassigned —</option>' + assigneeOptions;

    document.getElementById('filter-assignee').innerHTML =
      '<option value="">All Members</option>' + assigneeOptions;

  } catch (e) {
    console.error('Failed to load employees:', e);
  }
}

// ── Load tasks ─────────────────────────────────────────────
async function loadTasks() {
  try {
    allTasks = await apiFetch('/tasks?limit=500');
    updateStats();
    renderTable();
  } catch (e) {
    showToast('Failed to load tasks: ' + e.message, 'error');
    document.getElementById('task-tbody').innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">⚠️</div>
          <p>Could not connect to the API. Is the server running?</p>
        </div>
      </td></tr>`;
  }
}

// ── Stats ──────────────────────────────────────────────────
function updateStats() {
  const todo   = allTasks.filter(t => (t.status || 'To Do') === 'To Do').length;
  const inprog = allTasks.filter(t => t.status === 'In Progress').length;
  const done   = allTasks.filter(t => t.status === 'Done').length;

  document.getElementById('stat-total').textContent = allTasks.length;
  document.getElementById('stat-todo').textContent  = todo;
  document.getElementById('stat-inprog').textContent = inprog;
  document.getElementById('stat-done').textContent  = done;
}

// ── Filtering ──────────────────────────────────────────────
function filterByStatus(status) {
  activeStatusFilter = status;
  document.getElementById('filter-status').value = status;

  // Update sidebar active state
  ['nav-all','nav-todo','nav-inprog','nav-done','nav-dashboard'].forEach(id => {
    document.getElementById(id)?.classList.remove('active');
  });
  const map = { '': 'nav-all', 'To Do': 'nav-todo', 'In Progress': 'nav-inprog', 'Done': 'nav-done' };
  const targetNav = map[status] ?? 'nav-all';
  document.getElementById(targetNav)?.classList.add('active');

  // Update top bar title
  const titleMap = { '': 'All Tasks', 'To Do': 'To Do', 'In Progress': 'In Progress', 'Done': 'Done' };
  document.getElementById('topbar-title').textContent = titleMap[status] ?? 'All Tasks';

  applyFilters();
}

function applyFilters() {
  const search   = document.getElementById('search-input').value.toLowerCase();
  const status   = activeStatusFilter || document.getElementById('filter-status').value;
  const priority = document.getElementById('filter-priority').value;
  const assignee = document.getElementById('filter-assignee').value;

  let filtered = allTasks.filter(t => {
    const matchSearch = !search ||
      (t.title || '').toLowerCase().includes(search) ||
      (t.description || '').toLowerCase().includes(search);
    const matchStatus   = !status   || (t.status   || 'To Do')  === status;
    const matchPriority = !priority || (t.priority || 'Medium') === priority;
    const matchAssignee = !assignee || (t.assigned_to || '') === assignee;
    return matchSearch && matchStatus && matchPriority && matchAssignee;
  });

  filtered = sortTasks(filtered);
  renderRows(filtered);
}

// ── Sorting ────────────────────────────────────────────────
function sortTable(key) {
  if (sortKey === key) { sortAsc = !sortAsc; }
  else { sortKey = key; sortAsc = true; }

  // Update sort icons
  ['title','status','priority','assigned_to','created_at'].forEach(k => {
    document.getElementById(`sort-${k}`).textContent = '';
  });
  document.getElementById(`sort-${key}`).textContent = sortAsc ? '▲' : '▼';

  applyFilters();
}

function sortTasks(tasks) {
  return [...tasks].sort((a, b) => {
    let va = a[sortKey] ?? '';
    let vb = b[sortKey] ?? '';
    if (sortKey === 'created_at') { va = new Date(va); vb = new Date(vb); }
    else { va = String(va).toLowerCase(); vb = String(vb).toLowerCase(); }
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ?  1 : -1;
    return 0;
  });
}

// ── Render table ───────────────────────────────────────────
function renderTable() {
  applyFilters();
}

function renderRows(tasks) {
  const tbody = document.getElementById('task-tbody');

  if (tasks.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <p>No tasks found. Create one with the <strong>New Task</strong> button.</p>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = tasks.map(t => {
    const taskStatus   = t.status   || 'To Do';
    const taskPriority = t.priority || 'Medium';
    const safeTitle    = escHtml(t.title || '');
    const safeDesc     = escHtml(t.description || '');
    const safeAssignee = escHtml(t.assigned_to || '');

    return `
    <tr data-id="${t.id}">
      <td class="task-title-cell">
        <span class="task-title-text" title="${safeTitle}">${safeTitle}</span>
        ${safeDesc ? `<span class="task-desc" title="${safeDesc}">${safeDesc}</span>` : ''}
      </td>
      <td>${statusBadgeHtml(taskStatus)}</td>
      <td>${priorityHtml(taskPriority)}</td>
      <td>
        ${safeAssignee
          ? `<div class="assignee-cell">${avatarHtml(t.assigned_to)}<span>${safeAssignee}</span></div>`
          : '<span style="color:var(--text-muted);font-size:0.82rem">—</span>'}
      </td>
      <td style="color:var(--text-muted);font-size:0.82rem;white-space:nowrap">${fmtDate(t.created_at)}</td>
      <td class="action-cell">
        <button class="btn-edit" onclick="openEditModal(${t.id})">Edit</button>
        <button class="btn-del"  onclick="openDeleteModal(${t.id}, '${safeTitle}')">Delete</button>
      </td>
    </tr>`;
  }).join('');
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Create / Edit modal ────────────────────────────────────
function openCreateModal() {
  document.getElementById('task-id').value = '';
  document.getElementById('task-form').reset();
  document.getElementById('field-priority').value = 'Medium';
  document.getElementById('field-status').value   = 'To Do';
  document.getElementById('modal-title-text').textContent = 'New Task';
  document.getElementById('modal-submit-btn').textContent = 'Create Task';
  document.getElementById('task-modal').classList.add('open');
  document.getElementById('field-title').focus();
}

async function openEditModal(taskId) {
  try {
    const task = await apiFetch(`/tasks/${taskId}`);

    document.getElementById('task-id').value        = task.id;
    document.getElementById('field-title').value    = task.title || '';
    document.getElementById('field-desc').value     = task.description || '';
    document.getElementById('field-status').value   = task.status   || 'To Do';
    document.getElementById('field-priority').value = task.priority || 'Medium';
    document.getElementById('field-assignee').value = task.assigned_to || '';

    document.getElementById('modal-title-text').textContent = 'Edit Task';
    document.getElementById('modal-submit-btn').textContent = 'Save Changes';
    document.getElementById('task-modal').classList.add('open');
    document.getElementById('field-title').focus();
  } catch (e) {
    showToast('Failed to load task: ' + e.message, 'error');
  }
}

function closeModal() {
  document.getElementById('task-modal').classList.remove('open');
}

// ── Submit (create or update) ──────────────────────────────
async function submitTask(e) {
  e.preventDefault();
  const id       = document.getElementById('task-id').value;
  const title    = document.getElementById('field-title').value.trim();
  const desc     = document.getElementById('field-desc').value.trim();
  const status   = document.getElementById('field-status').value;
  const priority = document.getElementById('field-priority').value;
  const assignee = document.getElementById('field-assignee').value;

  const payload = {
    title,
    description: desc || null,
    status,
    priority,
    assigned_to: assignee || null,
  };

  const btn = document.getElementById('modal-submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    if (id) {
      // Update
      await apiFetch(`/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      showToast('Task updated successfully', 'success');
    } else {
      // Create
      await apiFetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({ ...payload, completed: false }),
      });
      showToast('Task created successfully', 'success');
    }
    closeModal();
    await loadTasks();
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = id ? 'Save Changes' : 'Create Task';
  }
}

// ── Delete modal ───────────────────────────────────────────
function openDeleteModal(taskId, taskTitle) {
  taskToDelete = taskId;
  document.getElementById('delete-task-name').textContent = taskTitle;
  document.getElementById('delete-modal').classList.add('open');
}

function closeDeleteModal() {
  taskToDelete = null;
  document.getElementById('delete-modal').classList.remove('open');
}

async function confirmDelete() {
  if (!taskToDelete) return;
  const btn = document.getElementById('confirm-delete-btn');
  btn.disabled = true;
  btn.textContent = 'Deleting…';
  try {
    await apiFetch(`/tasks/${taskToDelete}`, { method: 'DELETE' });
    showToast('Task deleted', 'success');
    closeDeleteModal();
    await loadTasks();
  } catch (err) {
    showToast('Failed to delete: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Delete Task';
  }
}

// ── Keyboard shortcuts ─────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeModal();
    closeDeleteModal();
  }
});

// Close modals when clicking backdrop
document.getElementById('task-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('task-modal')) closeModal();
});
document.getElementById('delete-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('delete-modal')) closeDeleteModal();
});

// ── Dashboard nav click ────────────────────────────────────
document.getElementById('nav-dashboard').addEventListener('click', () => {
  activeStatusFilter = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('topbar-title').textContent = 'Dashboard';
  ['nav-all','nav-todo','nav-inprog','nav-done'].forEach(id =>
    document.getElementById(id)?.classList.remove('active')
  );
  document.getElementById('nav-dashboard').classList.add('active');
  renderTable();
});

// ── Initialise ─────────────────────────────────────────────
(async function init() {
  await loadEmployees();
  await loadTasks();
})();

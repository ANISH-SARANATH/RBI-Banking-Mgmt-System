const healthStatus = document.getElementById('healthStatus');
const globalMessage = document.getElementById('globalMessage');

const adminAuthView = document.getElementById('adminAuthView');
const adminView = document.getElementById('adminView');
const adminHeading = document.getElementById('adminHeading');
const adminAccountsBody = document.getElementById('adminAccountsBody');

const money = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value);

const showMessage = (text, type = '') => {
  globalMessage.className = `notice${type ? ` ${type}` : ''}`;
  globalMessage.textContent = text;
};

const api = async (url, options = {}) => {
  const response = await fetch(url, options);
  let data = null;

  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || 'Request failed');
  }

  return data;
};

const switchView = (view) => {
  adminAuthView.classList.add('hidden');
  adminView.classList.add('hidden');
  view.classList.remove('hidden');
};

const loadAdminAccounts = async () => {
  const accounts = await api('/api/accounts');
  adminAccountsBody.innerHTML = '';

  if (accounts.length === 0) {
    adminAccountsBody.innerHTML = '<tr><td colspan="6">No accounts found.</td></tr>';
    return;
  }

  accounts.forEach((account) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${account.account_number}</td>
      <td>${account.holder_name}</td>
      <td>${account.email || '-'}</td>
      <td>${account.account_type}</td>
      <td>${money(account.balance)}</td>
      <td>${new Date(account.created_at).toLocaleDateString('en-IN')}</td>
    `;
    adminAccountsBody.appendChild(tr);
  });
};

document.getElementById('adminLoginForm').addEventListener('submit', async (event) => {
  event.preventDefault();

  try {
    const name = document.getElementById('adminName').value.trim();
    const password = document.getElementById('adminPassword').value;

    const result = await api('/api/auth/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, password }),
    });

    adminHeading.textContent = result.admin_name;
    switchView(adminView);
    await loadAdminAccounts();
    showMessage('Admin login successful', 'success');
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

document.getElementById('adminLogout').addEventListener('click', () => {
  switchView(adminAuthView);
  showMessage('Admin logged out', 'success');
});

const loadHealth = async () => {
  try {
    const response = await api('/api/health');
    healthStatus.textContent = response.status === 'ok' ? 'Server Online' : 'Server Error';
  } catch (_error) {
    healthStatus.textContent = 'Server Offline';
  }
};

(async () => {
  await loadHealth();
})();

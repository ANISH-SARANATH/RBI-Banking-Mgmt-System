const healthStatus = document.getElementById('healthStatus');
const accountCards = document.getElementById('accountCards');
const fromAccount = document.getElementById('fromAccount');
const toAccount = document.getElementById('toAccount');
const txnAccount = document.getElementById('txnAccount');
const txnBody = document.getElementById('txnBody');
const transferForm = document.getElementById('transferForm');
const transferMessage = document.getElementById('transferMessage');

let accounts = [];

const formatMoney = (value) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value);

const renderAccounts = () => {
  accountCards.innerHTML = '';

  accounts.forEach((account, index) => {
    const article = document.createElement('article');
    article.className = 'card account-card';
    article.style.animationDelay = `${index * 80}ms`;
    article.innerHTML = `
      <h4>${account.account_type}</h4>
      <p class="holder">${account.holder_name}</p>
      <p class="number">${account.account_number}</p>
      <p class="balance">${formatMoney(account.balance)}</p>
    `;
    accountCards.appendChild(article);
  });
};

const renderAccountOptions = () => {
  const options = accounts
    .map((account) => `<option value="${account.account_number}">${account.account_number} - ${account.holder_name}</option>`)
    .join('');

  fromAccount.innerHTML = options;
  toAccount.innerHTML = options;
  txnAccount.innerHTML = options;

  if (accounts.length > 1) {
    toAccount.value = accounts[1].account_number;
  }
};

const loadTransactions = async (accountNumber) => {
  txnBody.innerHTML = '<tr><td colspan="4">Loading...</td></tr>';

  const response = await fetch(`/api/accounts/${accountNumber}/transactions?limit=10`);
  const data = await response.json();

  if (!response.ok) {
    txnBody.innerHTML = `<tr><td colspan="4">${data.detail || 'Failed to load transactions'}</td></tr>`;
    return;
  }

  txnBody.innerHTML = '';

  if (data.length === 0) {
    txnBody.innerHTML = '<tr><td colspan="4">No transactions yet.</td></tr>';
    return;
  }

  data.forEach((txn) => {
    const row = document.createElement('tr');
    const typeClass = txn.txn_type === 'CREDIT' ? 'credit' : 'debit';
    const signedAmount = txn.txn_type === 'CREDIT' ? txn.amount : -txn.amount;
    row.innerHTML = `
      <td><span class="tag ${typeClass}">${txn.txn_type}</span></td>
      <td>${formatMoney(signedAmount)}</td>
      <td>${txn.description}</td>
      <td>${new Date(txn.created_at).toLocaleString('en-IN')}</td>
    `;
    txnBody.appendChild(row);
  });
};

const loadAccounts = async () => {
  const response = await fetch('/api/accounts');
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Failed to load accounts');
  }

  accounts = data;
  renderAccounts();
  renderAccountOptions();

  if (accounts.length > 0) {
    await loadTransactions(accounts[0].account_number);
  }
};

const loadHealth = async () => {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    if (response.ok && data.status === 'ok') {
      healthStatus.textContent = 'API Online';
    } else {
      healthStatus.textContent = 'API Error';
    }
  } catch (_error) {
    healthStatus.textContent = 'API Offline';
  }
};

transferForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  transferMessage.className = 'message';
  transferMessage.textContent = 'Processing transfer...';

  const payload = {
    from_account_number: fromAccount.value,
    to_account_number: toAccount.value,
    amount: Number(document.getElementById('amount').value),
    description: document.getElementById('description').value.trim(),
  };

  const response = await fetch('/api/transfers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const result = await response.json();

  if (!response.ok) {
    transferMessage.className = 'message error';
    transferMessage.textContent = result.detail || 'Transfer failed';
    return;
  }

  transferMessage.className = 'message success';
  transferMessage.textContent = `Transfer successful. Ref #${result.transfer_id}`;

  await loadAccounts();
  await loadTransactions(txnAccount.value || payload.from_account_number);
  transferForm.reset();
  if (accounts.length > 1) {
    fromAccount.value = accounts[0].account_number;
    toAccount.value = accounts[1].account_number;
  }
});

txnAccount.addEventListener('change', async (event) => {
  await loadTransactions(event.target.value);
});

(async () => {
  await loadHealth();
  try {
    await loadAccounts();
  } catch (error) {
    transferMessage.className = 'message error';
    transferMessage.textContent = error.message;
  }
})();

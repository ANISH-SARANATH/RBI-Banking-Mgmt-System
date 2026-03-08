const healthStatus = document.getElementById('healthStatus');
const globalMessage = document.getElementById('globalMessage');

const authView = document.getElementById('authView');
const customerView = document.getElementById('customerView');

const customerHeading = document.getElementById('customerHeading');
const customerSubline = document.getElementById('customerSubline');
const balanceValue = document.getElementById('balanceValue');
const minimumBalanceValue = document.getElementById('minimumBalanceValue');
const accountNumberValue = document.getElementById('accountNumberValue');

const transactionBody = document.getElementById('transactionBody');
const depositBody = document.getElementById('depositBody');
const contactInfo = document.getElementById('contactInfo');

const depositType = document.getElementById('depositType');
const frequencyField = document.getElementById('frequencyField');
const cardAction = document.getElementById('cardAction');
const cardNumberField = document.getElementById('cardNumberField');
const sendForms = document.getElementById('sendForms');
const loanEmailField = document.getElementById('loanEmailField');

const loginOtpField = document.getElementById('loginOtpField');
const loginOtpInput = document.getElementById('loginOtp');
const sendLoginOtpBtn = document.getElementById('sendLoginOtp');

const state = {
  customer: null,
  customerPassword: null,
  minimumBalance: 1000,
  pendingLogin: null,
};

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
  authView.classList.add('hidden');
  customerView.classList.add('hidden');
  view.classList.remove('hidden');
};

const resetLoginOtpState = () => {
  state.pendingLogin = null;
  loginOtpInput.value = '';
  loginOtpInput.required = false;
  loginOtpField.classList.add('hidden');
};

const renderTransactions = (rows) => {
  transactionBody.innerHTML = '';

  if (rows.length === 0) {
    transactionBody.innerHTML = '<tr><td colspan="4">No transactions yet.</td></tr>';
    return;
  }

  rows.forEach((txn) => {
    const tr = document.createElement('tr');
    const signed = txn.txn_type === 'CREDIT' ? txn.amount : -txn.amount;
    tr.innerHTML = `
      <td>${txn.txn_type}</td>
      <td>${money(signed)}</td>
      <td>${txn.description}</td>
      <td>${new Date(txn.created_at).toLocaleString('en-IN')}</td>
    `;
    transactionBody.appendChild(tr);
  });
};

const renderDeposits = (rows) => {
  depositBody.innerHTML = '';

  if (rows.length === 0) {
    depositBody.innerHTML = '<tr><td colspan="4">No deposits history yet.</td></tr>';
    return;
  }

  rows.forEach((dep) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${dep.deposit_type}</td>
      <td>${dep.frequency || '-'}</td>
      <td>${money(dep.amount)}</td>
      <td>${dep.expected_total ? money(dep.expected_total) : '-'}</td>
    `;
    depositBody.appendChild(tr);
  });
};

const loadContact = async () => {
  const info = await api('/api/contact');
  contactInfo.textContent = `Phone: ${info.phones.join(' / ')} | Email: ${info.email}`;
};

const refreshCustomerWorkspace = async () => {
  if (!state.customer) {
    return;
  }

  const accountNumber = state.customer.account_number;
  const account = await api(`/api/accounts/${accountNumber}`);
  const transactions = await api(`/api/accounts/${accountNumber}/transactions?limit=20`);
  const deposits = await api(`/api/accounts/${accountNumber}/deposits?limit=20`);

  customerHeading.textContent = account.holder_name;
  customerSubline.textContent = `Personal banking dashboard for account ${account.account_number}`;
  balanceValue.textContent = money(account.balance);
  minimumBalanceValue.textContent = money(state.minimumBalance);
  accountNumberValue.textContent = account.account_number;

  renderTransactions(transactions);
  renderDeposits(deposits);
  await loadContact();
};

const showCustomer = async (summary, password) => {
  state.customer = { account_number: summary.account_number, holder_name: summary.holder_name };
  state.customerPassword = Number(password);
  state.minimumBalance = summary.minimum_balance || 1000;

  switchView(customerView);
  await refreshCustomerWorkspace();
};

const requestLoginOtp = async (accountNumber, password, email = '') => {
  const payload = {
    account_number: accountNumber,
    password: Number(password),
  };

  if (email.trim()) {
    payload.email = email.trim().toLowerCase();
  }

  return api('/api/auth/customer/login/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
};

sendLoginOtpBtn.addEventListener('click', async () => {
  try {
    const accountNumber = document.getElementById('loginAccountNumber').value.trim();
    const passwordRaw = document.getElementById('loginPassword').value.trim();
    const password = Number(passwordRaw);
    const email = document.getElementById('loginEmail').value.trim();

    if (!accountNumber || !passwordRaw || Number.isNaN(password)) {
      showMessage('Enter account number and password before requesting OTP', 'error');
      return;
    }

    const result = await requestLoginOtp(accountNumber, password, email);
    state.pendingLogin = { accountNumber, password };
    loginOtpField.classList.remove('hidden');
    loginOtpInput.required = true;
    showMessage(`OTP sent to ${result.destination}. It is valid for 5 minutes.`, 'success');
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

document.getElementById('customerLoginForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const accountNumber = document.getElementById('loginAccountNumber').value.trim();
    const passwordRaw = document.getElementById('loginPassword').value.trim();
    const password = Number(passwordRaw);
    const otp = loginOtpInput.value.trim();

    if (!accountNumber || !passwordRaw || Number.isNaN(password)) {
      showMessage('Enter account number and password before verifying OTP', 'error');
      return;
    }

    if (!state.pendingLogin || state.pendingLogin.accountNumber !== accountNumber) {
      showMessage('Request OTP first for this account', 'error');
      return;
    }

    if (!otp || otp.length !== 6) {
      showMessage('Enter the 6-digit OTP from email', 'error');
      return;
    }

    const summary = await api('/api/auth/customer/login/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_number: accountNumber, password, otp }),
    });

    await showCustomer(summary, password);
    resetLoginOtpState();
    showMessage('Signed in successfully with email OTP', 'success');
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

document.getElementById('customerCreateForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const name = document.getElementById('createName').value.trim();
    const email = document.getElementById('createEmail').value.trim().toLowerCase();
    const openingBalance = Number(document.getElementById('createOpeningBalance').value);

    const created = await api('/api/auth/customer/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, opening_balance: openingBalance }),
    });

    document.getElementById('loginAccountNumber').value = created.account_number;
    document.getElementById('loginPassword').value = String(created.password);
    document.getElementById('loginEmail').value = created.email;

    const otpResult = await requestLoginOtp(created.account_number, created.password, created.email);
    state.pendingLogin = { accountNumber: created.account_number, password: created.password };
    loginOtpField.classList.remove('hidden');
    loginOtpInput.required = true;

    showMessage(
      `Account created. Account No: ${created.account_number}, Password: ${created.password}. OTP sent to ${otpResult.destination}.`,
      'success'
    );
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

document.getElementById('withdrawForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.customer) {
    return;
  }

  try {
    const amount = Number(document.getElementById('withdrawAmount').value);
    const result = await api(`/api/accounts/${state.customer.account_number}/withdraw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: state.customerPassword, amount }),
    });

    showMessage(`${result.message}. New balance: ${money(result.balance)}`, 'success');
    event.target.reset();
    await refreshCustomerWorkspace();
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

depositType.addEventListener('change', () => {
  frequencyField.classList.toggle('hidden', depositType.value !== 'RECURRING');
});

document.getElementById('depositForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.customer) {
    return;
  }

  try {
    const payload = {
      password: state.customerPassword,
      deposit_type: depositType.value,
      amount: Number(document.getElementById('depositAmount').value),
    };

    if (depositType.value === 'RECURRING') {
      payload.recurring_frequency = document.getElementById('recurringFrequency').value;
    }

    const result = await api(`/api/accounts/${state.customer.account_number}/deposit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const details = result.expected_total ? ` Expected total: ${money(result.expected_total)}` : '';
    showMessage(`${result.message}.${details}`, 'success');
    event.target.reset();
    frequencyField.classList.add('hidden');
    await refreshCustomerWorkspace();
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

cardAction.addEventListener('change', () => {
  const requiresCard = cardAction.value === 'ACTIVATE_OLD';
  cardNumberField.classList.toggle('hidden', !requiresCard);
  document.getElementById('cardNumber').required = requiresCard;
});

document.getElementById('cardForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.customer) {
    return;
  }

  try {
    const action = cardAction.value;
    const cardNumber = document.getElementById('cardNumber').value.trim();

    const payload = {
      password: state.customerPassword,
      card_type: document.getElementById('cardType').value,
      action,
      card_number: action === 'ACTIVATE_OLD' ? cardNumber : null,
    };

    const result = await api(`/api/accounts/${state.customer.account_number}/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    showMessage(`${result.message} (${result.status})`, 'success');
    event.target.reset();
    cardNumberField.classList.remove('hidden');
    document.getElementById('cardNumber').required = true;
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

sendForms.addEventListener('change', () => {
  loanEmailField.classList.toggle('hidden', !sendForms.checked);
  document.getElementById('loanEmail').required = sendForms.checked;
});

document.getElementById('loanForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.customer) {
    return;
  }

  try {
    const wantsForms = sendForms.checked;
    const payload = {
      password: state.customerPassword,
      loan_type: document.getElementById('loanType').value,
      phone: document.getElementById('loanPhone').value.trim(),
      send_forms: wantsForms,
      email: wantsForms ? document.getElementById('loanEmail').value.trim() : null,
    };

    const result = await api(`/api/accounts/${state.customer.account_number}/loans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const urlMessage = result.form_url ? ` Form URL: ${result.form_url}` : '';
    showMessage(`${result.message}${urlMessage}`, 'success');
    event.target.reset();
    loanEmailField.classList.add('hidden');
    document.getElementById('loanEmail').required = false;
  } catch (error) {
    showMessage(error.message, 'error');
  }
});

document.getElementById('customerLogout').addEventListener('click', () => {
  state.customer = null;
  state.customerPassword = null;
  resetLoginOtpState();
  switchView(authView);
  showMessage('Logged out', 'success');
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
  try {
    await loadContact();
  } catch (_error) {
    contactInfo.textContent = 'Contact details unavailable right now.';
  }
})();

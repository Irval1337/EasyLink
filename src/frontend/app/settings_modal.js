function togglePassword(btn) {
  const input = btn.parentNode.querySelector('input');
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.classList.add('text-indigo-300');
    btn.classList.remove('text-zinc-400');
  } else {
    input.type = 'password';
    btn.classList.remove('text-indigo-300');
    btn.classList.add('text-zinc-400');
  }
  btn.classList.add('scale-110');
  setTimeout(() => btn.classList.remove('scale-110'), 120);
}
function openSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) {
    modal.classList.remove('hidden');
    loadSettingsData();
  }
}

function closeSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) {
    modal.classList.add('hidden');
    clearSettingsForm();
  }
}

function loadSettingsData() {
  const emailInput = document.getElementById('settings-email');
  const usernameInput = document.getElementById('settings-username');
  const createdAt = document.getElementById('settings-created-at');
  const emailVerified = document.getElementById('settings-email-verified');
  const status = document.getElementById('settings-status');
  status.textContent = '';
  fetch('http://localhost/api/users/me', {
    headers: {
      'accept': 'application/json',
      'Authorization': 'Bearer ' + TokenManager.getToken()
    }
  })
    .then(res => res.json())
    .then(data => {
      emailInput.value = data.email || '';
      usernameInput.value = data.username || '';
      createdAt.textContent = 'Создан: ' + (data.created_at ? new Date(data.created_at).toLocaleString() : '—');
      emailVerified.innerHTML = data.email_verified ? '<span class="text-green-400">Email подтвержден</span>' : '<span class="text-red-400">Email не подтвержден</span>';
    })
    .catch(() => {
      status.textContent = 'Ошибка загрузки данных профиля';
      status.className = 'text-center text-sm text-red-400 mt-2';
    });
}

function clearSettingsForm() {
  document.getElementById('settings-form').reset();
  document.getElementById('settings-status').textContent = '';
}


function initSettingsModalEvents() {
  const form = document.getElementById('settings-form');
  if (form) {
    form.onsubmit = async function(e) {
      e.preventDefault();
      const email = document.getElementById('settings-email').value.trim();
      const username = document.getElementById('settings-username').value.trim();
      const password = document.getElementById('settings-password').value;
      const current_password = document.getElementById('settings-current-password').value;
      const status = document.getElementById('settings-status');
      status.textContent = '';
      status.className = 'text-center text-sm text-zinc-400 mt-2';
      if (!current_password) {
        status.textContent = 'Введите текущий пароль для подтверждения изменений';
        status.className = 'text-center text-sm text-red-400 mt-2';
        return;
      }
      const body = { email, username, current_password };
      if (password) body.password = password;
      try {
        const res = await fetch('http://localhost/api/users/me/update', {
          method: 'POST',
          headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + TokenManager.getToken()
          },
          body: JSON.stringify(body)
        });
        status.textContent = '';
        status.className = 'text-center text-sm mt-2';
        if (!res.ok) {
          let errText = 'Ошибка обновления профиля';
          try {
            const err = await res.json();
            if (err && err.detail) {
              if (typeof err.detail === 'string') {
                errText = translateProfileError(err.detail);
              } else if (typeof err.detail === 'object') {
                if (err.detail.message) {
                  errText = translateProfileError(err.detail.message);
                } else {
                  const first = Object.values(err.detail)[0];
                  if (typeof first === 'string') errText = translateProfileError(first);
                  else if (Array.isArray(first) && typeof first[0] === 'string') errText = translateProfileError(first[0]);
                  else {
                    errText = translateProfileError(JSON.stringify(err.detail));
                  }
                }
              }
            }
          } catch {}
          if (typeof showNotification === 'function') {
            showNotification(errText, 'error');
          }
          status.textContent = '';
          status.className = 'text-center text-sm mt-2';
          return;
        }
        if (typeof showNotification === 'function') {
          showNotification('Изменения успешно сохранены', 'success');
        }
        status.textContent = '';
        status.className = 'text-center text-sm mt-2';
        setTimeout(() => { window.location.reload(); }, 700);
      } catch (err) {
        let errText = 'Ошибка обновления профиля';
        if (err && err.message) {
          errText = translateProfileError(err.message);
        }
        if (typeof showNotification === 'function') {
          showNotification(errText, 'error');
        }
        status.textContent = '';
        status.className = 'text-center text-sm mt-2';
      }
function translateProfileError(msg) {
  if (!msg) return 'Ошибка';
  if (msg.includes('Current password is incorrect')) return 'Текущий пароль неверный';
  if (msg.includes('already exists') && msg.includes('email')) return 'Этот email уже используется';
  if (msg.includes('already exists') && msg.includes('username')) return 'Это имя пользователя уже занято';
  if (msg.includes('Password must be at least')) return 'Пароль слишком короткий';
  if (msg.includes('uppercase')) return 'Пароль должен содержать хотя бы одну заглавную букву';
  if (msg.includes('lowercase')) return 'Пароль должен содержать хотя бы одну строчную букву';
  if (msg.includes('digit')) return 'Пароль должен содержать хотя бы одну цифру';
  if (msg.includes('special character')) return 'Пароль должен содержать хотя бы один спецсимвол';
  if (msg.includes('Email is not verified')) return 'Email не подтвержден';
  if (msg.includes('Invalid credentials')) return 'Неверные учетные данные';
  if (msg.includes('User with')) return 'Пользователь не найден';
  if (msg.includes('Please wait')) return 'Слишком частые запросы на активацию email';
  if (msg.includes('Invalid email')) return 'Некорректный email';
  if (msg.includes('Invalid username')) return 'Некорректное имя пользователя';
  if (msg.includes('Invalid password')) return 'Некорректный пароль';
  if (msg.includes('No changes')) return 'Нет изменений';
  if (msg.includes('Internal server error')) return 'Внутренняя ошибка сервера';
  return msg;
}
    };
  }

  const logoutBtn = document.getElementById('logout-all-btn');
  if (logoutBtn) {
    logoutBtn.onclick = async function(e) {
      if (e) e.preventDefault();
      const status = document.getElementById('settings-status');
      status.textContent = '';
      try {
      const res = await fetch('http://localhost/api/users/logout', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Authorization': 'Bearer ' + TokenManager.getToken()
        }
      });
      if (!res.ok) throw new Error('Ошибка выхода со всех устройств');
      if (typeof showNotification === 'function') {
        showNotification('Вы вышли со всех устройств', 'success');
      }
      document.getElementById('settings-form').reset();
      setTimeout(() => { window.location.reload(); }, 700);
      } catch (err) {
        status.textContent = err.message || 'Ошибка выхода со всех устройств';
        status.className = 'text-center text-sm text-red-400 mt-2';
      }
    };
  }

  const closeBtn = document.getElementById('close-settings');
  if (closeBtn) {
    closeBtn.onclick = closeSettingsModal;
  }
}

window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;

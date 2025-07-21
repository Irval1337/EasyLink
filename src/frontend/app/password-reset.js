document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('reset-password-form');
  form.onsubmit = async function(e) {
    e.preventDefault();
    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-password');
    if (newPassword.value.length < 8) {
      showNotification('Пароль должен содержать минимум 8 символов', 'error');
      return;
    }
    if (newPassword.value !== confirmPassword.value) {
      showNotification('Пароли не совпадают', 'error');
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (!token) {
      showNotification('Некорректная ссылка для сброса пароля', 'error');
      return;
    }

    function translateResetError(message) {
      const translations = [
        { pattern: /expired|истек/i, text: 'Срок действия ссылки истёк. Запросите сброс заново.' },
        { pattern: /token.*invalid|invalid.*token|bad token|bad signature|signature.*invalid/i, text: 'Некорректная или устаревшая ссылка для сброса.' },
        { pattern: /password.*short|password.*weak|слишком короткий/i, text: 'Пароль слишком короткий или простой.' },
        { pattern: /password.*required|required/i, text: 'Введите новый пароль.' },
        { pattern: /not found|user.*not found|пользователь.*не найден/i, text: 'Пользователь не найден.' },
        { pattern: /mismatch|не совпад/i, text: 'Пароли не совпадают.' },
        { pattern: /server|internal/i, text: 'Ошибка сервера. Попробуйте позже.' },
        { pattern: /validation/i, text: 'Ошибка валидации. Проверьте введённые данные.' },
        { pattern: /too short/i, text: 'Слишком короткое значение.' },
        { pattern: /too long/i, text: 'Слишком длинное значение.' },
        { pattern: /required/i, text: 'Заполните обязательные поля.' },
        { pattern: /unknown/i, text: 'Неизвестная ошибка.' },
      ];
      for (const t of translations) {
        if (t.pattern.test(message)) return t.text;
      }
      return message;
    }

    try {
      const resp = await fetch('http://localhost/api/users/password-reset-confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword.value })
      });
      let data = {};
      try { data = await resp.json(); } catch {}
      if (resp.ok) {
        showNotification('Пароль успешно изменён! Теперь вы можете войти с новым паролем.', 'success');
        newPassword.value = '';
        confirmPassword.value = '';
      } else {
        const msg = data.detail || data.message || 'Ошибка сброса пароля';
        showNotification(translateResetError(msg), 'error');
      }
    } catch (err) {
      showNotification('Ошибка соединения с сервером', 'error');
    }
  };
});

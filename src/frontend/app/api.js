const API_CONFIG = {
  USERS_BASE_URL: 'http://localhost/api/users',
  URLS_BASE_URL: 'http://localhost/api/urls',
  ANALYTICS_BASE_URL: 'http://localhost/api/analytics'
};

class TokenManager {
  static getToken() {
    const sessionToken = sessionStorage.getItem('access_token');
    if (sessionToken) {
      return sessionToken;
    }
    const cookieToken = this.getCookie('access_token');
    if (cookieToken) {
      return cookieToken;
    }
    return localStorage.getItem('access_token');
  }

  static setToken(token) {
    this.setCookie('access_token', token, 7);
    localStorage.setItem('access_token', token);
    sessionStorage.removeItem('access_token');
  }

  static setSessionToken(token) {
    sessionStorage.setItem('access_token', token);
    this.deleteCookie('access_token');
    localStorage.removeItem('access_token');
  }

  static removeToken() {
    this.deleteCookie('access_token');
    localStorage.removeItem('access_token');
    sessionStorage.removeItem('access_token');
  }

  static isAuthenticated() {
    return !!this.getToken();
  }

  static getAuthHeaders() {
    const token = this.getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  static setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;secure;samesite=strict`;
  }

  static getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  }

  static deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
  }
}

class APIClient {
  static async makeRequest(url, options = {}) {
    const defaultHeaders = {
      'Content-Type': 'application/json',
      ...TokenManager.getAuthHeaders(),
    };

    const config = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
      mode: 'cors',
      credentials: 'include',
    };

    try {
      const response = await fetch(url, config);
      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        console.log('JSON parsing failed, trying text...', jsonError);
        const text = await response.text();
        console.log('Failed to parse JSON, using text:', text);
        data = { detail: text || `HTTP error! status: ${response.status}` };
      }

      if (response.status === 401) {
        TokenManager.removeToken();
      }

      if (!response.ok) {
        let errorMessage = 'Произошла неизвестная ошибка';
        let originalMessage = '';
        
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            originalMessage = data.detail.map(err => err.msg || err.type || 'Unknown error').join(', ');
          } else if (typeof data.detail === 'string') {
            originalMessage = data.detail;
          }
        } else if (data.message) {
          originalMessage = data.message;
        } else if (data.error) {
          originalMessage = data.error;
        }
        
        console.log('Исходное сообщение с сервера:', originalMessage);
        console.log('Полный объект data:', JSON.stringify(data, null, 2));
        
        const errorTranslations = {
          'Unauthorized': 'Неверный логин или пароль',
          'Invalid credentials': 'Неверный логин или пароль',
          'Could not validate credentials': 'Сессия истекла. Войдите заново',
          'Token expired': 'Сессия истекла. Войдите заново',
          'Access token expired': 'Сессия истекла. Войдите заново',
          
          'User not found': 'Пользователь не найден',
          'Email already exists': 'Этот email уже используется',
          'Username already exists': 'Это имя пользователя уже занято',
          'User already exists': 'Пользователь уже существует',
          'Please verify your email address before logging in': 'Сначала подтвердите email. Проверьте почту',
          'Email is not verified': 'Email не подтвержден. Проверьте почту',
          
          'Invalid email format': 'Некорректный формат email',
          'value is not a valid email address': 'Некорректный email адрес',
          'Password too short': 'Пароль слишком короткий (минимум 8 символов)',
          'Password must contain at least one uppercase letter': 'Пароль должен содержать заглавную букву',
          'Password must contain at least one lowercase letter': 'Пароль должен содержать строчную букву',
          'Password must contain at least one digit': 'Пароль должен содержать цифру',
          'String should have at least 8 characters': 'Минимум 8 символов',
          'field required': 'Обязательное поле',
          
          'Invalid URL format': 'Неверный формат ссылки',
          'URL too long': 'Ссылка слишком длинная',
          'Short code already exists': 'Такой короткий код уже существует',
          'URL not found': 'Ссылка не найдена',
          
          'Access denied': 'Доступ запрещен',
          'Rate limit exceeded': 'Слишком много запросов. Попробуйте позже',
          'Server error': 'Ошибка сервера. Попробуйте позже',
          'Network error': 'Проблемы с сетью. Проверьте интернет',
          'Internal server error': 'Внутренняя ошибка сервера',
          'Service unavailable': 'Сервис временно недоступен',
          
          'Email \'(.*?)\' already registered': 'Этот email уже зарегистрирован',
          'Username \'(.*?)\' already registered': 'Это имя пользователя уже занято',
          'Authentication failed': 'Ошибка авторизации',
          'Login failed': 'Не удалось войти в систему'
        };
        
        function translateError(errorText) {
          if (!errorText) return 'Произошла неизвестная ошибка';
          
          const lowerError = errorText.toLowerCase();
          
          if (lowerError.includes('unauthorized') || lowerError.includes('401')) {
            return 'Неверный логин или пароль';
          }
          
          if (lowerError.includes('email') && lowerError.includes('already')) {
            return 'Этот email уже используется';
          }
          
          if (lowerError.includes('username') && lowerError.includes('already')) {
            return 'Это имя пользователя уже занято';
          }
          
          if (lowerError.includes('email') && (lowerError.includes('verify') || lowerError.includes('not verified'))) {
            return 'Сначала подтвердите email. Проверьте почту';
          }
          
          if (lowerError.includes('token') && (lowerError.includes('expired') || lowerError.includes('invalid'))) {
            return 'Сессия истекла. Войдите заново';
          }
          
          if (lowerError.includes('rate limit')) {
            return 'Слишком много запросов. Попробуйте через минуту';
          }
          
          if (lowerError.includes('network') || lowerError.includes('fetch')) {
            return 'Проблемы с сетью. Проверьте интернет';
          }
          
          if (lowerError.includes('server error') || lowerError.includes('500')) {
            return 'Ошибка сервера. Попробуйте позже';
          }
          
          if (errorTranslations[errorText]) {
            return errorTranslations[errorText];
          }
          
          if (errorText.includes('already registered')) {
            if (errorText.includes('Email')) {
              return 'Этот email уже зарегистрирован';
            } else if (errorText.includes('Username')) {
              return 'Это имя пользователя уже занято';
            }
          }
          
          if (errorText.includes('Password must contain')) {
            if (errorText.includes('uppercase')) {
              return 'Пароль должен содержать заглавную букву';
            } else if (errorText.includes('lowercase')) {
              return 'Пароль должен содержать строчную букву';
            } else if (errorText.includes('digit')) {
              return 'Пароль должен содержать цифру';
            }
          }
          
          if (errorText.length > 100) {
            return 'Произошла ошибка. Попробуйте еще раз';
          }
          
          return errorText;
        }
        
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(err => {
              if (err.msg) {
                return translateError(err.msg);
              }
              return translateError(err.type) || err.type || 'Ошибка валидации';
            }).join(', ');
          } else if (typeof data.detail === 'string') {
            errorMessage = translateError(data.detail);
          }
        } else if (data.message) {
          errorMessage = translateError(data.message);
        } else if (data.error) {
          errorMessage = translateError(data.error);
        }
        
        if (response.status === 401 && (!errorMessage || errorMessage === 'Произошла неизвестная ошибка')) {
          errorMessage = 'Неверный логин или пароль';
        } else if (response.status === 403) {
          errorMessage = 'Доступ запрещен';
        } else if (response.status === 404) {
          errorMessage = 'Ресурс не найден';
        } else if (response.status === 422) {
          errorMessage = errorMessage || 'Проверьте правильность введенных данных';
        } else if (response.status === 429) {
          errorMessage = 'Слишком много запросов. Попробуйте через минуту';
        } else if (response.status >= 500) {
          errorMessage = 'Ошибка сервера. Попробуйте позже';
        } else if (response.status === 400) {
          errorMessage = errorMessage || 'Неверные данные';
        }
        
        const error = new Error(errorMessage);
        error.originalMessage = originalMessage;
        throw error;
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      console.log('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
      
      if (error.originalMessage !== undefined) {
        throw error;
      }
      
      if (error.name === 'TypeError' || error.message.includes('fetch')) {
        throw new Error('Не удается подключиться к серверу. Проверьте интернет');
      }
      
      if (error.message.includes('CORS')) {
        throw new Error('Ошибка доступа к серверу');
      }
      
      if (error.message.includes('timeout')) {
        throw new Error('Слишком долгий ответ сервера. Попробуйте еще раз');
      }
      throw error;
    }
  }

  static async makeAnonymousRequest(url, options = {}) {
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
      mode: 'cors',
      credentials: 'include',
    };

    try {
      const response = await fetch(url, config);
      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        console.log('JSON parsing failed, trying text...', jsonError);
        const text = await response.text();
        console.log('Failed to parse JSON, using text:', text);
        data = { detail: text || `HTTP error! status: ${response.status}` };
      }

      if (!response.ok) {
        let errorMessage = 'Произошла неизвестная ошибка';
        let originalMessage = '';
        
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            originalMessage = data.detail.map(err => err.msg || err.type || 'Unknown error').join(', ');
          } else if (typeof data.detail === 'string') {
            originalMessage = data.detail;
          }
        } else if (data.message) {
          originalMessage = data.message;
        } else if (data.error) {
          originalMessage = data.error;
        }
        
        if (response.status === 400) {
          errorMessage = originalMessage || 'Неверные данные запроса';
        } else if (response.status === 422) {
          errorMessage = originalMessage || 'Проверьте правильность введенных данных';
        } else if (response.status === 429) {
          errorMessage = 'Слишком много запросов. Попробуйте через минуту';
        } else if (response.status >= 500) {
          errorMessage = 'Ошибка сервера. Попробуйте позже';
        } else {
          errorMessage = originalMessage || 'Произошла ошибка';
        }
        
        const error = new Error(errorMessage);
        error.originalMessage = originalMessage;
        console.log('Anonymous request error:', { message: errorMessage, original: originalMessage });
        throw error;
      }

      return data;
    } catch (error) {
      console.error('Anonymous API request failed:', error);
      
      if (error.originalMessage !== undefined) {
        throw error;
      }
      
      if (error.name === 'TypeError' || error.message.includes('fetch')) {
        throw new Error('Не удается подключиться к серверу. Проверьте интернет');
      }
      
      if (error.message.includes('CORS')) {
        throw new Error('Ошибка доступа к серверу');
      }
      
      if (error.message.includes('timeout')) {
        throw new Error('Слишком долгий ответ сервера. Попробуйте еще раз');
      }
      
      throw error;
    }
  }

  static async register(userData) {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/register`, {
      method: 'POST',
      body: JSON.stringify({
        email: userData.email,
        username: userData.username,
        password: userData.password
      })
    });
  }

  static async login(credentials) {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/login`, {
      method: 'POST',
      body: JSON.stringify({
        identifier: credentials.identifier,
        password: credentials.password
      })
    });
  }

  static async logout() {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/logout`, {
      method: 'POST'
    });
  }

  static async getCurrentUser() {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/me`);
  }

  static async updateProfile(userData) {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/me/update`, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  static async verifyToken() {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/verify-token`, {
      method: 'POST'
    });
  }

  static async resendActivation(email) {
    return this.makeRequest(`${API_CONFIG.USERS_BASE_URL}/resend-activation`, {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  static async shortenUrl(urlData) {
    return this.makeRequest(`${API_CONFIG.URLS_BASE_URL}/shorten`, {
      method: 'POST',
      body: JSON.stringify(urlData)
    });
  }

  static async getMyUrls(params = {}) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        queryParams.append(key, value);
      }
    });

    const url = `${API_CONFIG.URLS_BASE_URL}/my${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.makeRequest(url);
  }

  static async updateUrl(urlId, updateData) {
    return this.makeRequest(`${API_CONFIG.URLS_BASE_URL}/${urlId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });
  }

  static async deactivateUrl(urlId) {
    return this.makeRequest(`${API_CONFIG.URLS_BASE_URL}/${urlId}/deactivate`, {
      method: 'PATCH'
    });
  }

  static async getUrlQrCode(urlId) {
    return this.makeRequest(`${API_CONFIG.URLS_BASE_URL}/${urlId}/qr`);
  }

  static async getPublicStats() {
    return this.makeRequest(`${API_CONFIG.ANALYTICS_BASE_URL}/public/stats`);
  }
}

class ErrorHandler {
  static handle(error, context = '') {
    console.error(`Error in ${context}:`, error);

    let message = 'Произошла ошибка. Попробуйте еще раз.';

    if (error.message === 'Unauthorized') {
      message = 'Необходимо войти в систему';
      return this.handleUnauthorized();
    }

    if (error.message.includes('validation')) {
      message = 'Проверьте правильность введенных данных';
    }

    if (error.message.includes('email')) {
      message = 'Пользователь с таким email уже существует';
    }

    if (error.message.includes('username')) {
      message = 'Пользователь с таким именем уже существует';
    }

    this.showError(message);
    return false;
  }

  static handleUnauthorized() {
    TokenManager.removeToken();
    showNotification('Необходимо войти в систему', 'error');
    const loginModal = document.getElementById('login-modal');
    if (loginModal && typeof openModal === 'function') {
      openModal(loginModal);
    }
    return false;
  }

  static showError(message) {
    if (typeof showNotification === 'function') {
      showNotification(message, 'error');
    } else {
      alert(message);
    }
  }
}

class UserManager {
  static currentUser = null;

  static async loadCurrentUser() {
    if (!TokenManager.isAuthenticated()) {
      return null;
    }

    try {
      this.currentUser = await APIClient.getCurrentUser();
      return this.currentUser;
    } catch (error) {
      console.error('Error loading current user:', error);
      return null;
    }
  }

  static getCurrentUser() {
    return this.currentUser;
  }

  static isLoggedIn() {
    return TokenManager.isAuthenticated() && this.currentUser;
  }

  static async logout() {
    try {
      await APIClient.logout();
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      TokenManager.removeToken();
      this.currentUser = null;
      this.updateUI();
    }
  }

  static updateUI() {
    if (typeof updateUserInterface === 'function') {
      updateUserInterface(this.isLoggedIn());
    }
  }
}

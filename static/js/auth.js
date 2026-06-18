// Handle Register Form
const registerForm = document.getElementById('registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
      name: registerForm.name.value,
      email: registerForm.email.value,
      password: registerForm.password.value
    };

    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await res.json();

      if (res.ok) {
        alert('Registration successful!');
        window.location.href = '/login';
      } else {
        alert(data.error || 'Registration failed');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
}

// Handle Login Form
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
      email: loginForm.email.value,
      password: loginForm.password.value
    };

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await res.json();

      if (res.ok) {
        alert('Login successful!');
        localStorage.setItem('token', data.token);
        window.location.href = '/dashboard'; // Next page you’ll create
      } else {
        alert(data.error || 'Login failed');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
}

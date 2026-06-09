(function () {
  function ensureNavLayout(nav) {
    if (!nav) return { left: null, right: null };

    var existingLeft = nav.querySelector('.nav-left');
    var existingRight = nav.querySelector('.nav-right');
    if (existingLeft && existingRight) {
      return { left: existingLeft, right: existingRight };
    }

    var children = Array.from(nav.children);
    var left = document.createElement('div');
    var right = document.createElement('div');
    left.className = 'nav-left';
    right.className = 'nav-right';

    nav.innerHTML = '';
    nav.appendChild(left);
    nav.appendChild(right);

    children.forEach(function (child) {
      if (child.id === 'userWelcome' || child.id === 'authButtons') {
        right.appendChild(child);
      } else {
        left.appendChild(child);
      }
    });

    return { left: left, right: right };
  }

  function ensureContactLink(nav) {
    if (!nav) return;
    var groups = ensureNavLayout(nav);
    var left = groups.left;
    if (!left) return;
    if (left.querySelector('a[data-nav-contact="true"]')) return;

    var contactLink = document.createElement('a');
    contactLink.href = '/about#contact-section';
    contactLink.textContent = 'Contact Us';
    contactLink.setAttribute('data-nav-contact', 'true');

    left.appendChild(contactLink);
  }

  function isProtectedPage() {
    return document.body && document.body.dataset.requireLogin === 'true';
  }

  function getUserName() {
    return localStorage.getItem('userName') || '';
  }

  function renderAuth() {
    var nav = document.querySelector('.navbars');
    var userWelcome = document.getElementById('userWelcome');
    var authButtons = document.getElementById('authButtons');

    if (!userWelcome || !authButtons) return;

    if (nav) {
      var groups = ensureNavLayout(nav);
      if (groups.right) {
        groups.right.appendChild(userWelcome);
        groups.right.appendChild(authButtons);
      }
    }

    ensureContactLink(nav);

    var storedLogin = localStorage.getItem('isLoggedIn') === 'true';
    var userName = getUserName();
    var loggedIn = isProtectedPage() || storedLogin || Boolean(userName);

    if (loggedIn) {
      userWelcome.innerHTML = '<span class="user-icon" aria-hidden="true"></span>' +
        '<span>Hi, ' + (userName || 'Member') + '</span>' +
        '<button onclick="handleLogout()" class="nav-btn logout-btn">Logout</button>';
      userWelcome.style.display = 'inline-flex';
      authButtons.style.display = 'none';
      return;
    }

    userWelcome.style.display = 'none';
    authButtons.innerHTML = '<a href="/login" class="nav-btn">Login</a><a href="/register" class="nav-btn">Register</a>';
    authButtons.style.display = 'inline-flex';
  }

  window.handleLogout = function handleLogout() {
    if (!confirm('Are you sure you want to logout?')) return;
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userName');
    window.location.href = '/logout';
  };

  document.addEventListener('DOMContentLoaded', renderAuth);
})();

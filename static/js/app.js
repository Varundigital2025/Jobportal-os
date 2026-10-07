/**
 * JobPortal Core Client Application JavaScript
 * Provides UI interactivity: mobile navigation, modals, flash messages,
 * AJAX bookmarking, and confirmation alerts.
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileMenu();
  initFlashDismissal();
  initModals();
  initSaveJobButtons();
  initPasswordToggles();
  initConfirmDialogs();
});

/**
 * Mobile Navigation Toggle
 */
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobile-menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');

  if (toggleBtn && mobileMenu) {
    toggleBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });
  }
}

/**
 * Flash Notification Auto-dismiss and Close Handlers
 */
function initFlashDismissal() {
  const alerts = document.querySelectorAll('.flash-alert');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.remove();
      });
    }

    // Auto dismiss after 6 seconds
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
      }
    }, 6000);
  });
}

/**
 * Generic Modal Controls
 */
function initModals() {
  // Modal open triggers: elements with data-modal-target="modal-id"
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = trigger.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.classList.add('overflow-hidden');
      }
    });
  });

  // Modal close triggers: elements with data-modal-close
  document.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
      const modal = closeBtn.closest('.modal-backdrop');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.classList.remove('overflow-hidden');
      }
    });
  });

  // Close when clicking modal backdrop outside content
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.classList.remove('overflow-hidden');
      }
    });
  });
}

/**
 * AJAX Save/Bookmark Job Handler
 */
function initSaveJobButtons() {
  document.querySelectorAll('.btn-save-job').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const jobId = btn.getAttribute('data-job-id');
      const saveUrl = `/jobs/${jobId}/save`;

      try {
        const response = await fetch(saveUrl, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        });

        if (response.redirected) {
          window.location.href = response.url;
          return;
        }

        const data = await response.json();
        if (data.success) {
          const icon = btn.querySelector('.save-icon');
          const label = btn.querySelector('.save-label');
          const navCounter = document.getElementById('saved-jobs-counter');

          if (data.saved) {
            btn.classList.add('saved-active');
            if (icon) {
              icon.classList.remove('fa-regular');
              icon.classList.add('fa-solid');
              icon.classList.add('text-rose-500');
            }
            if (label) label.textContent = 'Saved';
          } else {
            btn.classList.remove('saved-active');
            if (icon) {
              icon.classList.remove('fa-solid', 'text-rose-500');
              icon.classList.add('fa-regular');
            }
            if (label) label.textContent = 'Save';
          }

          // Show floating toast message
          showToast(data.message, data.saved ? 'success' : 'info');
        }
      } catch (err) {
        console.error('Save job failed:', err);
      }
    });
  });
}

/**
 * Toast Notification Popup
 */
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'success' ? 'bg-emerald-600' : (type === 'danger' ? 'bg-rose-600' : 'bg-slate-800');
  toast.className = `${bgClass} text-white text-sm px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 pointer-events-auto transition-all duration-300 opacity-0 translate-y-2`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-circle-info'}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.remove('opacity-0', 'translate-y-2');
    toast.classList.add('opacity-100', 'translate-y-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/**
 * Password Visibility Toggle
 */
function initPasswordToggles() {
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetInput = document.querySelector(btn.getAttribute('data-target'));
      if (targetInput) {
        const isPassword = targetInput.type === 'password';
        targetInput.type = isPassword ? 'text' : 'password';
        const icon = btn.querySelector('i');
        if (icon) {
          icon.classList.toggle('fa-eye', !isPassword);
          icon.classList.toggle('fa-eye-slash', isPassword);
        }
      }
    });
  });
}

/**
 * Confirmation dialogs for destructive actions
 */
function initConfirmDialogs() {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      const msg = el.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
}

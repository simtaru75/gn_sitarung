// === dokumen ===
      if (document.body.dataset.page === "dokumen") {
      // Mockup interactions
document.querySelectorAll('.checkbox').forEach(cb => {
  cb.addEventListener('click', () => cb.classList.toggle('checked'));
});
document.querySelectorAll('.filter-chip').forEach(chip => {
  chip.addEventListener('click', () => chip.classList.toggle('active'));
});
document.querySelectorAll('.drawer-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.drawer-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
  });
});
document.querySelector('.drawer-close')?.addEventListener('click', () => {
  document.querySelector('.drawer').style.display = 'none';
});
      }

// === dokumen_baru ===
      if (document.body.dataset.page === "dokumen_baru") {
      // Simple form interactions
document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(el => {
  el.addEventListener('input', () => {
    // Visual feedback only — real progress logic on backend
  });
});
      }

// === dokumen_detail ===
      if (document.body.dataset.page === "dokumen_detail") {
      // Section collapse toggle
document.querySelectorAll('.ds-collapse').forEach(b => b.addEventListener('click', () => {
  b.closest('.doc-section').classList.toggle('collapsed');
}));
// Workflow step click (visual only)
document.querySelectorAll('.wf-step').forEach(s => s.addEventListener('click', () => {
  document.querySelectorAll('.wf-step').forEach(x => x.classList.remove('current'));
  s.classList.add('current');
}));
// Suggested tag chips on click promote to regular
document.querySelectorAll('.multi-tag.suggested').forEach(t => t.addEventListener('click', () => {
  t.classList.remove('suggested');
  t.innerHTML = t.textContent.replace('+ ', '') + ' <span class="x">×</span>';
}));
      }

// === data_spasial ===
      if (document.body.dataset.page === "data_spasial") {
      document.querySelectorAll('.perm-check').forEach(c => c.addEventListener('click', () => c.classList.toggle('checked')));
document.querySelectorAll('.filter-chip').forEach(c => c.addEventListener('click', () => c.classList.toggle('active')));
document.querySelector('.drawer-close')?.addEventListener('click', () => {
  document.querySelector('.drawer').style.display = 'none';
});
      }

// === layer_edit ===
      if (document.body.dataset.page === "layer_edit") {
      document.querySelectorAll('.ds-collapse').forEach(b => b.addEventListener('click', () => {
  b.closest('.doc-section').classList.toggle('collapsed');
}));
document.querySelectorAll('.wf-step').forEach(s => s.addEventListener('click', () => {
  document.querySelectorAll('.wf-step').forEach(x => x.classList.remove('current'));
  s.classList.add('current');
}));
document.querySelectorAll('.ogc-pill:not(.disabled-perm)').forEach(p =>
  p.addEventListener('click', () => p.classList.toggle('active'))
);
      }

// === akses_nasional ===
      if (document.body.dataset.page === "akses_nasional") {
      document.querySelectorAll('.toggle, .endpoint-toggle').forEach(t =>
  t.addEventListener('click', () => t.classList.toggle('on'))
);
document.querySelectorAll('.format-opt').forEach(f =>
  f.addEventListener('click', () => f.classList.toggle('active'))
);
// Toggle disabled card when endpoint-toggle clicked
document.querySelectorAll('.endpoint-toggle').forEach(t =>
  t.addEventListener('click', () => {
    const card = t.closest('.endpoint-card');
    card.classList.toggle('disabled', !t.classList.contains('on'));
  })
);
      }

// === endpoint_api ===
      if (document.body.dataset.page === "endpoint_api") {
      // Tab toggling
document.querySelectorAll('.detail-tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.detail-tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.codebox-tab').forEach(t => t.addEventListener('click', (e) => {
  const tabs = e.target.parentElement.querySelectorAll('.codebox-tab');
  tabs.forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.response-tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.response-tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.env-tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.env-tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.nav-item').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.nav-group-header').forEach(h =>
  h.addEventListener('click', () => h.closest('.nav-group').classList.toggle('collapsed'))
);
      }

// === metadata_schema ===
      if (document.body.dataset.page === "metadata_schema") {
      document.querySelectorAll('.toggle-switch').forEach(t => t.addEventListener('click', () => t.classList.toggle('on')));
document.querySelectorAll('.editor-tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.editor-tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
}));
document.querySelectorAll('.tree-field').forEach(f => f.addEventListener('click', () => {
  document.querySelectorAll('.tree-field').forEach(x => x.classList.remove('active'));
  f.classList.add('active');
}));
document.querySelectorAll('.tree-group-header').forEach(h => h.addEventListener('click', () => {
  h.closest('.tree-group').classList.toggle('collapsed');
}));
      }


// === pengguna ===
      if (document.body.dataset.page === "pengguna") {
      document.querySelectorAll('.toggle').forEach(t =>
  t.addEventListener('click', () => t.classList.toggle('on'))
);
document.querySelectorAll('.filter-chip').forEach(c =>
  c.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
  })
);
      }

// === pengaturan ===
      if (document.body.dataset.page === "pengaturan") {
      // Toggle interactions
document.querySelectorAll('.toggle').forEach(t =>
  t.addEventListener('click', () => t.classList.toggle('on'))
);
// Palette chip selection (single)
document.querySelectorAll('.palette-chip').forEach(c =>
  c.addEventListener('click', () => {
    document.querySelectorAll('.palette-chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
  })
);
// memotong jumlah karakter
  document.querySelectorAll('.ds-meta-row strong').forEach(function(el) {
    var text = el.textContent.trim();
    if (text.length > 15) {
      el.textContent = text.slice(0, 15) + '…';
    }
  });
// In-page nav active state on scroll
const sections = document.querySelectorAll('.settings-section[id]');
const navLinks = document.querySelectorAll('.page-nav-list a[href^="#"]');
function updateActiveNav() {
  let current = '';
  sections.forEach(s => {
    const rect = s.getBoundingClientRect();
    if (rect.top <= 120) current = s.id;
  });
  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === '#' + current) link.classList.add('active');
  });
}
window.addEventListener('scroll', updateActiveNav, { passive: true });
// Smooth scroll
navLinks.forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
      }




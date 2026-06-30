document.querySelectorAll('.layer-chip').forEach(chip => {
  chip.addEventListener('click', () => chip.classList.toggle('active'));
});

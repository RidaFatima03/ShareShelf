function wireModal({
  openBtnId,
  modalId,
  closeSelector,
  focusSelector
}) {
  const openBtn = document.getElementById(openBtnId);
  const modal = document.getElementById(modalId);
  const closeElems = document.querySelectorAll(closeSelector);

  if (openBtn && modal) {
    openBtn.addEventListener("click", () => {
      modal.classList.add("show");
      const el = focusSelector ? modal.querySelector(focusSelector) : null;
      if (el) setTimeout(() => el.focus(), 100);
    });
  }

  closeElems.forEach(el => el.addEventListener("click", () => modal.classList.remove("show")));
}

function wireEditButtons({
  buttonSelector,
  modalId,
  map,            // {datasetKey: inputId}
  focusInputId
}) {
  const modal = document.getElementById(modalId);
  const buttons = document.querySelectorAll(buttonSelector);

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      Object.entries(map).forEach(([datasetKey, inputId]) => {
        const input = document.getElementById(inputId);
        if (input) input.value = btn.dataset[datasetKey] || "";
      });
      modal.classList.add("show");
      const focusEl = document.getElementById(focusInputId);
      if (focusEl) setTimeout(() => focusEl.focus(), 100);
    });
  });
}

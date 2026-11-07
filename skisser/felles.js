// Legger til sidemeny og toppmeny (GUI-002) i hver .ha-ramme, slik at
// sidene slipper å gjenta den samme markupen. Rammen angir aktiv fane med
// data-tab="status|general|appliances|charging".

const TABS = [
  { id: "status", icon: "◉", label: "Status" },
  { id: "general", icon: "⚙", label: "Generelt" },
  { id: "appliances", icon: "☰", label: "Apparater" },
  { id: "charging", icon: "⚡", label: "Billading" },
];

function sidebarHtml() {
  return `
    <nav class="sidebar" aria-hidden="true">
      <div class="s-item">⌂</div>
      <div class="s-item">▦</div>
      <div class="s-item active" title="Kraftvakt">⏻</div>
      <div class="s-item">⚙</div>
    </nav>`;
}

function toolbarHtml(activeTab) {
  const tabs = TABS.map(
    (t) => `<div class="tab${t.id === activeTab ? " active" : ""}">
              <span class="ico">${t.icon}</span><span class="lbl">${t.label}</span>
            </div>`
  ).join("");
  return `
    <div class="toolbar">
      <span class="menu">≡</span>
      <span class="title">Kraftvakt</span>
      <div class="tabs">${tabs}</div>
      <span class="spacer"></span>
    </div>`;
}

for (const frame of document.querySelectorAll(".ha[data-tab]")) {
  const main = document.createElement("div");
  main.className = "main";
  main.innerHTML = toolbarHtml(frame.dataset.tab);
  while (frame.firstChild) main.appendChild(frame.firstChild);
  frame.insertAdjacentHTML("afterbegin", sidebarHtml());
  frame.appendChild(main);
}

// Rammer med dialog gjøres høye nok til at hele dialogen synes.
for (const dialog of document.querySelectorAll(".ha .dialog")) {
  const frame = dialog.closest(".ha");
  frame.style.minHeight = `${dialog.offsetHeight + 64}px`;
}

(function () {
  "use strict";

  const mobileQuery = window.matchMedia("(max-width: 600px)");

  function reset(message, icon) {
    message.classList.remove("is-collapsible", "is-expanded");
    message.removeAttribute("role");
    message.removeAttribute("tabindex");
    message.removeAttribute("aria-expanded");
    message.removeAttribute("aria-controls");
    message.onclick = null;
    message.onkeydown = null;
    icon.hidden = true;
  }

  function initializeMaintenanceToggle() {
    const message = document.querySelector("[data-maintenance-toggle]");
    if (!message) {
      return;
    }

    const text = message.querySelector(".maintenance__text");
    const icon = message.querySelector(".maintenance__icon");
    if (!text || !icon) {
      return;
    }

    reset(message, icon);
    if (!mobileQuery.matches) {
      return;
    }

    message.classList.add("is-collapsible");
    if (text.scrollHeight <= text.clientHeight + 1) {
      message.classList.remove("is-collapsible");
      return;
    }

    message.setAttribute("role", "button");
    message.setAttribute("tabindex", "0");
    message.setAttribute("aria-expanded", "false");
    message.setAttribute("aria-controls", text.id);
    icon.hidden = false;

    const setExpanded = (expanded) => {
      message.classList.toggle("is-expanded", expanded);
      message.setAttribute("aria-expanded", String(expanded));
    };

    message.onclick = () => {
      setExpanded(message.getAttribute("aria-expanded") !== "true");
    };

    message.onkeydown = (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      message.click();
    };
  }

  document.addEventListener("DOMContentLoaded", initializeMaintenanceToggle);
  window.addEventListener("resize", initializeMaintenanceToggle);
})();

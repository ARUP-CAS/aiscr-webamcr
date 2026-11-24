// Loads the remaining rows of a related-record table on a detail page (button "Načíst zbývající záznamy").
// The server returns only rows past the display limit inside tbody[data-radky="<klic>"]; they are appended here.
(() => {
    // Modal options for row action buttons, keyed by button class (same options as the page-level binders).
    const ROW_MODALS = {
        "file-smazat-btn": "smazat-soubor-form",
        "file-prejmenovat-btn": "prejmenovat-soubor-form",
        "dokument-odpojit-btn": "odpojit-dokument-form",
        "ez-odpojit-btn": "odpojit-az-form",
        "ez-change-btn": "zmenit-eo-form",
    };

    const bindRowModals = (rows) => {
        rows.forEach((row) => {
            Object.entries(ROW_MODALS).forEach(([cls, formID]) => {
                row.querySelectorAll("." + cls).forEach((el) => {
                    // Modal re-resolves the button by id; skip when that would not find this exact element.
                    if (!el.id || document.getElementById(el.id) !== el) {
                        console.info("Row action button not bound to a modal (missing or duplicate id):", el);
                        return;
                    }
                    const options = Object.assign(Object.create(defaults), {
                        modalID: "modal-form",
                        formID: formID,
                        modalFormID: "#" + formID,
                    });
                    new Modal(options, el.id);
                });
            });
        });
    };

    document.addEventListener("click", (event) => {
        const button = event.target.closest(".app-nacist-zbyvajici-btn");
        if (!button || button.disabled) {
            return;
        }
        button.disabled = true;
        const selector = 'tbody[data-radky="' + CSS.escape(button.dataset.klic) + '"]';
        const scope = button.closest(".card") || document;
        fetch(button.dataset.url, { credentials: "same-origin" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.text();
            })
            .then((html) => {
                const source = new DOMParser().parseFromString(html, "text/html").querySelector(selector);
                const target = scope.querySelector(selector);
                if (!source || !target) {
                    throw new Error("Rows for " + selector + " not found");
                }
                const rows = Array.from(source.children).map((row) =>
                    target.appendChild(document.importNode(row, true))
                );
                bindRowModals(rows);
                button.closest(".app-nacist-zbyvajici").remove();
                target.dispatchEvent(new CustomEvent("amcr:radky-nacteny", { bubbles: true, detail: { rows: rows } }));
            })
            .catch((error) => {
                console.error(error);
                button.disabled = false;
            });
    });
})();

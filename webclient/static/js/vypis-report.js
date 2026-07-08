(function () {
    function toggleSimpleView() {
        const wrapper = document.getElementById('app-wrapper');
        if (!wrapper) {
            return;
        }

        const toggle = document.getElementById('simple-view-toggle');
        const label = document.getElementById('simple-view-toggle-label');
        if (!toggle || !label) {
            return;
        }

        const simpleLabel = toggle.dataset.simpleLabel || '';
        const fullLabel = toggle.dataset.fullLabel || '';
        const simpleViewEnabled = wrapper.classList.toggle('simple-view');

        label.textContent = simpleViewEnabled ? fullLabel : simpleLabel;
        toggle.setAttribute('aria-label', simpleViewEnabled ? fullLabel : simpleLabel);
        toggle.checked = simpleViewEnabled;

        document.querySelectorAll('#app-wrapper .not-simple').forEach((section) => {
            const previous = section.previousElementSibling;
            if (previous && previous.tagName === 'HR') {
                previous.style.display = simpleViewEnabled ? 'none' : '';
            }
        });
    }

    function createRtf() {
        const wrapper = document.getElementById('app-wrapper');
        if (!wrapper) {
            return;
        }

        const exportRoot = wrapper.cloneNode(true);

        if (wrapper.classList.contains('simple-view')) {
            exportRoot.querySelectorAll('.not-simple').forEach((section) => {
                const previous = section.previousElementSibling;
                if (previous && previous.tagName === 'HR') {
                    previous.remove();
                }
                section.remove();
            });
        }

        const htmlContent = exportRoot.outerHTML;
        const vypisPrefix = 'AMCR_vypis';
        const currentDateTime = new Date();
        const year = currentDateTime.getFullYear();
        const month = String(currentDateTime.getMonth() + 1).padStart(2, '0');
        const day = String(currentDateTime.getDate()).padStart(2, '0');
        const hours = String(currentDateTime.getHours()).padStart(2, '0');
        const minutes = String(currentDateTime.getMinutes()).padStart(2, '0');
        const seconds = String(currentDateTime.getSeconds()).padStart(2, '0');
        const formattedDate = `${year}${month}${day}_${hours}${minutes}${seconds}`;
        const htmlToRtfLocal = new window.htmlToRtf();
        let rtfContent = htmlToRtfLocal.convertHtmlToRtf(htmlContent);
        rtfContent = rtfContent.replace(/ \\\'20/g, "\\\'20");
        const blob = new Blob([rtfContent], { type: 'application/rtf' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${vypisPrefix}_${formattedDate}.rtf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    window.toggleSimpleView = toggleSimpleView;
    window.createRtf = createRtf;
})();

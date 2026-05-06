// Anonymní flow oznámení: pokud se uživatel v jiném okně mezitím přihlásil,
// Django rotuje CSRF cookie a token vyrenderovaný do formuláře by nesouhlasil.
// Před odesláním POST formuláře přepíšeme hodnotu skrytého pole csrfmiddlewaretoken
// aktuální hodnotou z cookie.
(function () {
    function getCsrfCookie() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : null;
    }

    function refreshTokens() {
        const token = getCsrfCookie();
        if (!token) return;
        document.querySelectorAll('form[method="post" i] input[name="csrfmiddlewaretoken"]')
            .forEach(function (input) { input.value = token; });
    }

    document.addEventListener('submit', function (e) {
        if (e.target && e.target.tagName === 'FORM'
            && (e.target.getAttribute('method') || '').toLowerCase() === 'post') {
            refreshTokens();
        }
    }, true);
})();

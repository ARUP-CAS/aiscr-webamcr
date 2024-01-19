function initializeTooltips() {
    $('[rel="tooltip"]').tooltip({
        container: '#app-page-wrapper',
        html: true,
    });
}

window.onload = function () {
    inputs = document.querySelectorAll("input[type=text]");
    for (index = 0; index < inputs.length; ++index) {
        if (inputs[index].readOnly === true) {
            inputs[index].title = inputs[index].value
            inputs[index].setAttribute("data-toggle", "tooltip")
            inputs[index].setAttribute("data-placement", "top")
            inputs[index].setAttribute("rel", "tooltip")
        }
    }
    textareas = document.querySelectorAll("textarea");
    for (index = 0; index < textareas.length; ++index) {
        if (inputs[index].readOnly === true) {
            textareas[index].title = textareas[index].value
            textareas[index].setAttribute("data-toggle", "tooltip")
            textareas[index].setAttribute("data-placement", "top")
            inputs[index].setAttribute("rel", "tooltip")
        }
    }
    initializeTooltips()
}

window.onload = function () {
    const inputs = document.querySelectorAll("input[type=text]");
    for (let index = 0; index < inputs.length; ++index) {
        if (inputs[index].readOnly === true) {
            inputs[index].title = inputs[index].value
            inputs[index].setAttribute("data-bs-toggle", "tooltip")
            inputs[index].setAttribute("data-bs-placement", "top")
            inputs[index].setAttribute("rel", "tooltip")
        }
    }
    const textareas = document.querySelectorAll("textarea");
    for (let index = 0; index < textareas.length; ++index) {
        if (textareas[index].readOnly === true) {
            textareas[index].title = textareas[index].value
            textareas[index].setAttribute("data-bs-toggle", "tooltip")
            textareas[index].setAttribute("data-bs-placement", "top")
            textareas[index].setAttribute("rel", "tooltip")
        }
    }
    const elements = document.querySelectorAll("[name*='visible_x']");
    for (let index = 0; index < elements.length; ++index) {
        const element = elements[index]
        if (element.disabled) {
            element.title = element.value
            element.setAttribute("data-bs-toggle", "tooltip")
            element.setAttribute("data-bs-placement", "top")
            element.setAttribute("rel", "tooltip")
        }
    }
    // Re-initialize tooltips if new elements were added dynamically
    if (window.reinitializeTooltips) {
        window.reinitializeTooltips();
    }
}

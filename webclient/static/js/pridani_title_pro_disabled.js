window.onload = function () {
    inputs = document.querySelectorAll("input[type=text]");
    for (index = 0; index < inputs.length; ++index) {
        inputs[index].title = inputs[index].value
    }
    textareas = document.querySelectorAll("textarea");
    for (index = 0; index < textareas.length; ++index) {
        textareas[index].title = textareas[index].value
    }
}
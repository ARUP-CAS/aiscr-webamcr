window.onload = function () {
    inputs = document.querySelectorAll("input[type=text]");
    for (index = 0; index < inputs.length; ++index) {
        inputs[index].title = inputs[index].value
    }
}
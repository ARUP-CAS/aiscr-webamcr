function ChangeFields(checked_field, fields, allowed, required,) {
    var allowed_now = []
    if (typeof allowed.get(checked_field.value) != "undefined") {
        allowed_now = allowed.get(checked_field.value)
    }
    var required_now = []
    if (typeof required.get(checked_field.value) != "undefined") {
        required_now = required.get(checked_field.value)
    }
    for ([key, value] of fields) {
        if (allowed_now.includes(key)) {
            enableField(key, checked_field, fields, required_now.includes(key))
        }
        else {
            disableField(key, fields)
        }
    }
};


function disableField(id, fields) {
    element = document.getElementById(id)
    element.required = false;
    if (element.type == 'select-multiple' || element.type == 'select-one') {
        label = element.parentElement.parentElement.parentElement.getElementsByTagName("label")[0]
        if (label == null) {
            label = element.parentElement.parentElement.parentElement.parentElement.getElementsByTagName("label")[0]
        }
        select_id = "#" + id
        if (element.disabled == false) {
            fields.set(key, $(select_id).val());
        }
        $(select_id).prop("disabled", true);
        $(select_id).selectpicker('deselectAll');
        $(select_id).selectpicker('refresh');
        element.classList.remove("required-next")
        if (label.getElementsByTagName("span").length > 0) {
            label.getElementsByTagName("span")[0].remove()
        }
    }
    else {
        label = element.parentElement.parentElement.getElementsByTagName("label")[0]
        element.classList.remove("required-next")
        fields.set(key, element.value);
        if (element.disabled == false) {
            element.value = "";
        }
        if (label.getElementsByTagName("span").length > 0) {
            label.getElementsByTagName("span")[0].remove()
        }
    }
    element.disabled = true;
};

function enableField(id, checked_field, fields, required_field) {
    element = document.getElementById(id)
    if (element.type != 'select-multiple' || element.type != 'select-one') {
        label = element.parentElement.parentElement.parentElement.getElementsByTagName("label")[0]
        if (label == null) {
            label = element.parentElement.parentElement.parentElement.parentElement.getElementsByTagName("label")[0]
        }
        if (checked_field.required == true) {
            select_id = "#" + id
            if (element.disabled == true) {
                $(select_id).val(fields.get(key));
            }
            $(select_id).prop("disabled", false);
            $(select_id).selectpicker('render');
            $(select_id).selectpicker('refresh');
            if (required_field) {
                label.classList.add("requiredField");
                element.required = true;
                if (!element.classList.contains("required-next")) {
                    element.classList.add("required-next")
                }
                if (label.getElementsByTagName("span").length == 0) {
                    label.insertAdjacentHTML("beforeend", '<span class="asteriskField">*</span>')
                }
            }
        };
    }
    else {
        label = element.parentElement.parentElement.getElementsByTagName("label")[0]
        if (checked_field.required == true) {
            if (element.disabled == true) {
                element.value = fields.get(key);
            }
            if (required_field) {
                element.required = true;
                label.classList.add("requiredField");
                if (!element.classList.contains("required-next")) {
                    element.classList.add("required-next")
                }
                if (label.getElementsByTagName("span").length == 0) {
                    label.insertAdjacentHTML("beforeend", '<span class="asteriskField">*</span>')
                }
            }
        };
    }
    element.disabled = false;
};
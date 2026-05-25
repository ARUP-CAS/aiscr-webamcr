function changeFields(checked_field, fields, allowed, required,) {
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
        $(select_id).val("").trigger('change');
        $(select_id).prop("disabled", true);
        if (!(element.classList.contains("select2multiple"))) {
            // destroy+reinit místo refresh kvůli chybě bootstrap-select 1.14.0-beta3
            // (buildData duplikuje položky v nabídce), viz #3957 / #3917.
            $(select_id).selectpicker('destroy').selectpicker();
        }
        if (!(element.classList.contains("select2multiple"))) {
            element.classList.remove("required-next")
        }
        else {
            element.parentElement.getElementsByClassName("select2-selection")[0].classList.remove("required-next")
        }
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
        select_id = "#" + id
        if (element.disabled == true) {
            $(select_id).val(fields.get(key)).trigger('change');
        }
        $(select_id).prop("disabled", false);
        // destroy+reinit místo refresh kvůli chybě bootstrap-select 1.14.0-beta3
        // (buildData duplikuje položky v nabídce), viz #3957 / #3917. Jen pro skutečné
        // selecty – tato větev se kvůli BUG-016 spouští i pro textová pole, na ta se
        // selectpicker volat nesmí (refresh na nich byl beztak jen no-op).
        if (!(element.classList.contains("select2multiple"))
            && (element.type == 'select-multiple' || element.type == 'select-one')) {
            $(select_id).selectpicker('destroy').selectpicker();
        }
        if (checked_field.required == true) {
            if (required_field) {
                label.classList.add("requiredField");
                element.required = true;
                if (!(element.classList.contains("select2multiple"))) {
                    if (!element.classList.contains("required-next")) {
                        element.classList.add("required-next")
                    }
                }
                else {
                    if (!element.parentElement.getElementsByClassName("select2-selection")[0].classList.contains("required-next")) {
                        element.parentElement.getElementsByClassName("select2-selection")[0].classList.add("required-next")
                    }
                }
                if (label.getElementsByTagName("span").length == 0) {
                    label.insertAdjacentHTML("beforeend", '<span class="asteriskField">*</span>')
                }
            }
        };
    }
    else {
        label = element.parentElement.parentElement.getElementsByTagName("label")[0]
        if (element.disabled == true) {
            element.value = fields.get(key);
        }
        if (checked_field.required == true) {
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
(function ($) {

    // Open modal & load the form at formURL to the modalContent element
    var modalForm = function (settings) {
        $(settings.modalID).find(settings.modalContent).load(settings.formURL, function () {
            $(settings.modalID).modal("show");
            $(settings.modalForm).attr("action", settings.formURL);
            addEventHandlers(settings);
        });
    };

    var addEventHandlers = function (settings) {
        $(settings.modalForm).on("submit", function (event) {
            if (event.originalEvent !== undefined && settings.isDeleteForm === false) {
                event.preventDefault();
                isFormValid(settings, submitForm);
                return false;
            }
        });
        // Modal close handler
        $(settings.modalID).on("hidden.bs.modal", function (event) {
            $(settings.modalForm).remove();
        });
    };

    // Check if form.is_valid() & either show errors or submit it via callback
    var isFormValid = function (settings, callback) {
        $.ajax({
            type: $(settings.modalForm).attr("method"),
            url: $(settings.modalForm).attr("action"),
            data: new FormData($(settings.modalForm)[0]),
            contentType: false,
            processData: false,
            beforeSend: function () {
                $(settings.submitBtn).prop("disabled", true);
            },
            success: function (response) {
                if ($(response).find(settings.errorClass).length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalID).find(settings.modalContent).html(response);
                    $(settings.modalForm).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    addEventHandlers(settings);
                } else if ($(response).find(".alert-block").length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalID).find(settings.modalContent).html(response);
                    $(settings.modalForm).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    addEventHandlers(settings);
                }
                 else {
                     if (response.messages.length > 0) {
                        console.log(response.messages)
                        createMessage(response.messages)
                     }
                    // Form is valid, submit it
                    succesFunction(settings, response);
                }
            }
        });
    };

    // Submit form callback function
    var submitForm = function (settings) {        
        if (!settings.asyncUpdate) {
            $(settings.modalForm).submit();
        }
    };

    var succesFunction = function (settings, response) {
        if (!settings.successFunc) {
            $(settings.modalID).modal("hide");
        } else {
            settings.successFunc(settings, response)
        }
    };
    // asi pak pouzit jednu funkci ktera je v AMCR-1
    var createMessage = function (messages) {
        html = `<div class="alert alert-${messages[0].extra_tags} alert-dismissible fade show app-alert-floating" role="alert">
        ${messages[0].message}
        <button aria-label="Close" class="close" data-dismiss="alert" type="button">
        <span aria-hidden="true">&times;</span></button></div>`
        $('.message-container').append(html);
    }

    $.fn.modalForm = function (options) {
        // Default settings
        var defaults = {
            modalID: "#modal",
            modalContent: ".modal-content",
            modalForm: ".modal-content form",
            formURL: null,
            isDeleteForm: false,
            errorClass: ".invalid",
            successFunc: successFunction
        };

        // Extend default settings with provided options
        var settings = $.extend(defaults, options);

        this.each(function () {
            // Add click event handler to the element with attached modalForm
            $(this).click(function (event) {
                // Instantiate new form in modal
                modalForm(settings);
            });
        });

        return this;
    };

}(jQuery));
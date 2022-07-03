var defaults = {
    modalID: "modal",
    modalContent: ".modal-content",
    modalForm: ".modal-content form",
    formURL: null,
    isDeleteForm: false,
    errorClass: ".is-invalid",
    successFunc: false,
    errorFunc: false,
    createSuccesMessage: true,
    formID : "form-id",
    modalIDD : "#modal-form",
    firstModalID: false,
    secondModal: false,
    modalFormID: "#create-osoba-form",
};

class Modal {
    constructor(settings,button){
        this.button = document.getElementById(button),
        this.modalIDD = settings.modalIDD,
        this.modalID = settings.modalID,
        this.modalContent= settings.modalContent,
        this.modalForm= settings.modalForm,
        this.formID = settings.formID,
        this.formURL= settings.formURL,
        this.isDeleteForm= settings.isDeleteForm,
        this.errorClass= settings.errorClass,
        this.successFunc= settings.successFunc,
        this.createSuccesMessage= settings.createSuccesMessage
        this.firstModalID = settings.firstModalID,
        this.secondModal = settings.secondModal,
        this.modalFormID = settings.modalFormID,
        this.hidden = false,
        this.init()
    }

    init(){
        this.event = new CustomEvent('modalLoaded')
        this.button.addEventListener("click",this);
    }

    clickEvent(e){
        if (this.button.attributes.href){
            this.formURL = this.button.attributes.href.value;
        }
        //var modal = document.getElementById(this.modalID)
        //this.modalElement = modal.getElementsByClassName(this.modalContent)[0]
        this.getForm()
        
    }

    getForm (){
        var object = this
        $(this.modalIDD).find(this.modalContent).load(this.formURL, function (response, status, xhr) {
            if (xhr.status == "403"){
                window.location.href = JSON.parse(response).redirect
            }
            else {
                $(object.modalIDD).on('show.bs.modal', function(){
                    object.resetScripts()
                    if (!object.secondModal){
                        window.dispatchEvent(object.event);
                    }
                    if (object.firstModalID){
                        object.secondModal.hidden = true
                        $(object.firstModalID).modal("hide");
                    }
                });
                $(object.modalIDD).modal("show");
                $(object.modalFormID).attr("action", object.formURL);
                object.addEventHandlers(object)
            }
        });
    }

    addEventHandlers (settings) {
        var object = settings
        $(settings.modalFormID).on("submit", function (event) {
            if (event.originalEvent !== undefined) {
                event.preventDefault();
                object.isFormValid(object);
                event.stopImmediatePropagation();
                return false;
            }
        });
        // Modal close handler
        $(settings.modalIDD).on("hidden.bs.modal", function (event) {
            if (object.hidden) {
            }
            else if (object.firstModalID && !object.hidden){
                $(object.modalForm).remove();
                $(object.firstModalID).modal("show");
                object.secondModal.hidden = false;
            }
            else {
                $(object.modalFormID).remove();
            }
        });
    };

    isFormValid (settings, callback) {
        $.ajax({
            type: $(settings.modalFormID).attr("method"),
            url: $(settings.modalFormID).attr("action"),
            data: new FormData($(settings.modalFormID)[0]),
            async: false,
            contentType: false,
            processData: false,
            beforeSend: function () {
                $("#submit-btn").prop("disabled", true);
            },
            success: function (response) {
                if ($(response).find(settings.errorClass).length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalIDD).find(settings.modalContent).html(response);
                    $(settings.modalFormID).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    settings.addEventHandlers(settings);
                    settings.resetScripts();
                } else if ($(response).find(".alert-block").length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalIDD).find(settings.modalContent).html(response);
                    $(settings.modalFormID).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    settings.addEventHandlers(settings);
                    settings.resetScripts();
                }
                 else {
                     // Form is valid
                     if (response.messages) {
                        console.log("somthing11")
                        if (settings.createSuccesMessage === true){
                            console.log("somthing")
                            createMessage(response.messages[0].extra_tags,response.messages[0].message)
                        }
                     }
                     settings.succesFunction(settings,response)
                }
            },
            error: function (response) {
                settings.errorFunction(settings,response)
            }
        });
    }

    succesFunction (settings, response) {
        if (!settings.successFunc) {
            if (response.redirect){
                window.location.href = response.redirect
            }
            else{
                $(settings.modalIDD).modal("hide");
            }
        } else {
            settings.successFunc(settings, response)
        }
    };

    errorFunction (settings, response) {
        if (!settings.errorFunc) {
            if (response.redirect){
                window.location.href = response.redirect
            }
            else if (response.messages) {
                createMessage(response.messages[0].extra_tags,response.messages[0].message)
                $(settings.modalIDD).modal("hide");
            }
            else{
                location.reload(); 
            }
         }
        else{
            settings.errorFunc(settings, response)
        }
    };

    handleEvent(e) {
        switch(e.type) {
            case "click":
                this.clickEvent(e);
        }
    }

    resetScripts(){
        $('.selectpicker').selectpicker('refresh');
        $(".dateinput").datepicker({
            format: "dd.mm.yyyy",
            language: 'cs',
            todayHighlight: true,
            endDate: new Date(2100,12,31)
        });
    }
}
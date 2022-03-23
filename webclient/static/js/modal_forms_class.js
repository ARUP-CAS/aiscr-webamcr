var defaults = {
    modalID: "modal",
    modalContent: ".modal-content",
    modalForm: ".modal-content form",
    formURL: null,
    isDeleteForm: false,
    errorClass: ".invalid",
    successFunc: false,
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
        console.log(button)
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
        //this.button.addEventHandler("click", this.init_modal)
    }

    init_modal(){
        $(this.modalID).find(this.modalContent).load(this.formURL, function (response, status, xhr) {
            if (xhr.status == "403"){
                window.location.href = JSON.parse(response).redirect
            }
            $(this.modalID).modal("show");
            document.getElementById(this.formID).action=settings.formURL;
            console.log(this.event);
            window.dispatchEvent(this.event);
            addEventHandlers(settings);
        });
    }

    clickEvent(e){
        console.log("clicked button")
        var modal = document.getElementById(this.modalID)
        console.log(modal)
        //this.modalElement = modal.getElementsByClassName(this.modalContent)[0]
        this.getForm()
        
        //addEventHandlers(settings);
    }

    getForm (){
        var object = this
        $(this.modalIDD).find(this.modalContent).load(this.formURL, function (response, status, xhr) {
            if (xhr.status == "403"){
                window.location.href = JSON.parse(response).redirect
            }
            $(object.modalIDD).on('show.bs.modal', function(){
                document.getElementById(object.formID).action=object.formURL;
                $('.selectpicker').selectpicker('refresh');
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
        });
    }

    addEventHandlers (settings) {
        var object = settings
        $(settings.modalFormID).on("submit", function (event) {
            if (event.originalEvent !== undefined) {
                console.log("submiting")
                event.preventDefault();
                object.isFormValid(object);
                return false;
            }
        });
        // Modal close handler
        $(settings.modalIDD).on("hidden.bs.modal", function (event) {
            if (object.hidden) {
                console.log("Not closing")
            }
            else if (object.firstModalID && !object.hidden){
                console.log("Removing not hidden")
                $(object.modalForm).remove();
                $(object.firstModalID).modal("show");
                object.secondModal.hidden = false;
            }
            else {
                console.log("Removing")
                $(object.modalFormID).remove();
            }
        });
    };

    isFormValid (settings, callback) {
        $.ajax({
            type: $(settings.modalFormID).attr("method"),
            url: $(settings.modalFormID).attr("action"),
            data: new FormData($(settings.modalFormID)[0]),
            contentType: false,
            processData: false,
            beforeSend: function () {
                console.log("beforesend")
                $(settings.submitBtn).prop("disabled", true);
            },
            success: function (response) {
                if ($(response).find(settings.errorClass).length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalIDD).find(settings.modalContent).html(response);
                    $(settings.modalFormID).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    settings.addEventHandlers(settings);
                } else if ($(response).find(".alert-block").length > 0) {
                    // Form is not valid, update it with errors
                    $(settings.modalIDD).find(settings.modalContent).html(response);
                    $(settings.modalFormID).attr("action", settings.formURL);
                    // Reinstantiate handlers
                    console.log("allert block")
                    settings.addEventHandlers(settings);
                }
                 else {
                     // Form is valid
                     console.log("valid")
                     if ($(response).find("messages").length > 0) {
                        if (settings.createSuccesMessage === true){
                            createMessage(response.messages[0].extra_tags,response.messages[0].message)
                        }
                     }
                     settings.succesFunction(settings,response)
                }
            },
            error: function (response) {
                window.location.href = response.redirect
            }
        });
    }

    succesFunction (settings, response) {
        if (!settings.successFunc) {
            console.log("success")
            window.location.href = response.redirect
        } else {
            settings.successFunc(settings, response)
        }
    };

    handleEvent(e) {
        switch(e.type) {
            case "click":
                this.clickEvent(e);
        }
    }



}
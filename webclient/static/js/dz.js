Dropzone.autoDiscover = false;
const get_params = () => {
    if (typeof object_id !== 'undefined') {
        return { 'objectID': object_id };
    }
    if (typeof file_id !== 'undefined') {
        return { 'fileID': file_id };
    }
    return {}
};
const get_description = () => {
    if (typ_uploadu == 'upload') {
        return [dz_trans["descriptionUpload"]]; // Přiložte dokumentaci
    }
    if (typ_uploadu == 'nahradit') {
        return [dz_trans["descriptionNahradit"]]; // Přiložte aktualizovaný soubor
    }
    return "";
};

const UploadResultsEnum = {
    success: 0,
    duplicate: 1,
    reject: 2,
    error: 3,
}

const show_upload_successful_message = (file, result = UploadResultsEnum.success, message = "") => {
    const collection = document.getElementsByClassName("message-container");
    if (collection.length > 0) {
        const message_container_element = collection[0];
        // <div class="alert alert-success alert-dismissible fade show app-alert-floating" role="alert">
        const alert_element = document.createElement("div");
        const sidebar_element_query = document.getElementsByClassName("app-sidebar-wrapper");
        const floating_class = sidebar_element_query.length > 0 ? "app-alert-floating-file-upload" : "app-alert-floating-file-upload-oznameni";
        if (result === UploadResultsEnum.success) {
            alert_element.setAttribute("class", `alert alert-success alert-dismissible fade show ${floating_class}`);
        } else if (result === UploadResultsEnum.duplicate) {
            alert_element.setAttribute("class", `alert alert-warning alert-dismissible fade show ${floating_class}`);
        } else if (result === UploadResultsEnum.reject || result === UploadResultsEnum.error) {
            alert_element.setAttribute("class", `alert alert-danger alert-dismissible fade show ${floating_class}`);
        }
        alert_element.setAttribute("role", "alert");
        if (result === UploadResultsEnum.success) {
            alert_element.textContent = [dz_trans["alertsUpload_succesfullPart_1"]] + file.name + [dz_trans["alertsUpload_succesfullPart_2"]];
        } else if (result === UploadResultsEnum.duplicate) {
            alert_element.textContent = message;
        } else if (result === UploadResultsEnum.reject) {
            alert_element.textContent = [dz_trans["alertsUpload_rejectPart_1"]] + file.name + [dz_trans["alertsUpload_rejectPart_2"]] + message;
        } else if (result === UploadResultsEnum.error) {
            alert_element.textContent = [dz_trans["alertsUpload_errorPart_1"]] + file.name + [dz_trans["alertsUpload_errorPart_2"]] + message;
        }
        const button_element = document.createElement("button");
        button_element.setAttribute('type', 'button');
        button_element.setAttribute('class', 'close');
        button_element.setAttribute('data-dismiss', 'alert');
        button_element.setAttribute('aria-label', 'Close');
        const span_element = document.createElement("span");
        span_element.setAttribute('aria-hidden', 'true');
        span_element.innerHTML = "&times;";
        button_element.appendChild(span_element);
        alert_element.appendChild(button_element);
        message_container_element.appendChild(alert_element);
    }
}

window.onload = function () {
    const xhttp = new XMLHttpRequest();
    var csrfcookie = function () {
        var cookieValue = null,
            name = 'csrftoken';
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    var currentLocation = window.location.pathname;
    if (currentLocation.includes("soubor/nahrat/pas/")) {
        acceptFile = "image/*"
        RejectedFileMessage = reject_dict["rejected_pas"] //pridat do message constants po merge AMCR-1 a otestovat
    } else if (currentLocation.includes("soubor/nahrat/dokument/")) {
        acceptFile = ".jpeg, " +
            ".JPEG, " +
            ".jpg, " +
            ".JPG, " +
            ".png, " +
            ".PNG, " +
            ".tiff, " +
            ".TIFF, " +
            ".tif, " +
            ".TIF, " +
            ".txt, " +
            ".TXT, " +
            ".pdf, " +
            ".PDF, " +
            ".csv, " +
            ".CSV"
        RejectedFileMessage = reject_dict["rejected_dokument"]
    } else {
        acceptFile = "image/*, " +
            ".zip, " +
            ".ZIP, " +
            ".rar, " +
            ".RAR, " +
            ".7z, " +
            ".7Z, " +
            "application/vnd.ms-excel, " +
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document, " +
            "application/docx, " +
            "application/pdf, " +
            "text/plain, " +
            "application/msword, " +
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, " +
            "application/vnd.oasis.opendocument.text, " +
            "application/vnd.oasis.opendocument.spreadsheet "
        RejectedFileMessage = reject_dict["rejected_all"]
    }
    var dropzoneOptions = {
        dictDefaultMessage: get_description(),
        acceptedFiles: acceptFile,
        dictInvalidFileType: RejectedFileMessage,
        addRemoveLinks: true,
        dictCancelUpload: [dz_trans["cancelUpload"]],
        dictCancelUploadConfirmation: [dz_trans["cancelUploadConfirm"]],
        dictRemoveFile: [dz_trans["removeFile"]],
        maxFilesize: 100, // MB
        maxFiles: maxFiles,
        addRemoveLinks: addRemoveLinks,
        parallelUploads: 1,
        timeout: 10000000,
        init: function () {
            this.on("success", function (file, response) {
                file.id = response.id
                file.previewElement.lastChild.style.display = null
                if (response.duplicate) {
                    show_upload_successful_message(file, UploadResultsEnum.duplicate, response.duplicate);
                    console.log("success > " + file.name);

                } else {
                    show_upload_successful_message(file, UploadResultsEnum.success);
                }
            });
            this.on("removedfile", function (file) {
                if (file.id) {
                    xhttp.open("POST", "/soubor/smazat/" + typ_vazby + "/" + object_id + "/" + file.id);
                    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                    xhttp.setRequestHeader('X-CSRFToken', csrfcookie());
                    xhttp.send("dropzone=true");
                }
            });
            this.on("sending", function (file) {
                file.previewElement.lastChild.style.display = "none"
            });

        },
        error: function (file, response) {
            console.log(response);
            if (Array.isArray(response) && response.includes('reject')) {
                show_upload_successful_message(file, UploadResultsEnum.reject, response);
            }
            else if (response.hasOwnProperty("error")) {
                show_upload_successful_message(file, UploadResultsEnum.error, response.error);
            } else {
                show_upload_successful_message(file, UploadResultsEnum.error);
            }

            this.removeFile(file);

        },
        params: get_params(),
    };
    var uploader = document.querySelector('#my-awesome-dropzone');
    var newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

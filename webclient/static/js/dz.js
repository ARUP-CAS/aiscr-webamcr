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
    renamed: 4,
    duplicate_renamed: 4,
}

const check_sidebar_state = () => {
    const width = screen.width;
    const app_wrapper = document.getElementById("app-sidebar-wrapper");
    if (app_wrapper) {
        const style = window.getComputedStyle(app_wrapper) || app_wrapper.currentStyle;
        const margin_left = style.marginLeft;
        return margin_left === "-300px"
    }
    return false;
}

const show_upload_successful_message = (file, result = UploadResultsEnum.success, message = "") => {
    const collection = document.getElementsByClassName("message-container");
    if (collection.length > 0) {
        const sidebar_affected_class = check_sidebar_state() ? "app-alert-floating-file-upload-no-left-bar " : "";
        const message_container_element = collection[0];
        // <div class="alert alert-success alert-dismissible fade show app-alert-floating" role="alert">
        const alert_element = document.createElement("div");
        const sidebar_element_query = document.getElementsByClassName("app-sidebar-wrapper");
        const floating_class = sidebar_element_query.length > 0 ? "app-alert-floating-file-upload" : "app-alert-floating-file-upload-oznameni";
        const alert_common_classes = "alert alert-success alert-dismissible fade show app-alert-floating-file-upload";
        if (result === UploadResultsEnum.success) {
            const alert_status_class = "alert-success";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class}`);
        } else if (result === UploadResultsEnum.duplicate || result === UploadResultsEnum.renamed || result === UploadResultsEnum.duplicate_renamed) {
            const alert_status_class = "alert-warning";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class}`);
        } else if (result === UploadResultsEnum.reject || result === UploadResultsEnum.error) {
            const alert_status_class = "alert-danger";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class} ${message}`);
        }
        alert_element.setAttribute("role", "alert");
        if (result === UploadResultsEnum.success) {
            alert_element.textContent = `${dz_trans["alertsUploadSuccesfullPart1"]} ${file.name} ${dz_trans["alertsUploadSuccesfullPart2"]}`;
        } else if (result === UploadResultsEnum.duplicate || result === UploadResultsEnum.renamed || result === UploadResultsEnum.duplicate_renamed) {
            alert_element.textContent = message;
        } else if (result === UploadResultsEnum.reject) {
            alert_element.textContent = `${dz_trans["alertsUploadRejectPart1"]} ${file.name} ${dz_trans["alertsUploadRejectPart2"]}${message}`;
        } else if (result === UploadResultsEnum.error) {
            alert_element.textContent = `${dz_trans["alertsUploadErrorPart1"]} ${file.name} ${dz_trans["alertsUploadErrorPart2"]}${message}`;
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
    const csrfcookie = function () {
        let cookieValue = null,
            name = 'csrftoken';
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    const currentLocation = window.location.pathname;
    let acceptFile = null;
    let RejectedFileMessage = null;
    if (currentLocation.includes("soubor/nahrat/pas/")) {
        acceptFile = "image/jpeg, " +
            "image/png, " +
            "image/tiff, " +
            "image/heic, " +
            "image/heif"
        RejectedFileMessage = reject_dict["rejected_pas"]
    } else if (currentLocation.includes("soubor/nahrat/dokument/")) {
        acceptFile = "image/jpeg, " +
            "image/png, " +
            "image/tiff, " +
            "image/svg+xml, " +
            "text/plain, " +
            "application/pdf, " +
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, " +
            "text/csv"
        RejectedFileMessage = reject_dict["rejected_dokument"]
    } else if (currentLocation.includes("soubor/nahrat/model3d/")) {
        acceptFile = "image/jpeg, " +
            "image/png, " +
            "image/tiff, " +
            "image/svg+xml, " +
            "application/pdf, " +
            "application/zip, " +
            "application/zip-compressed, " +
            "application/x-zip-compressed, " +
            "application/vnd.rar, " +
            "application/x-rar, " +
            "application/x-rar-compressed, " +
            "application/x-compressed," +
            "application/x-7z-compressed"
        RejectedFileMessage = reject_dict["rejected_dokument_model"]
    } else {
        acceptFile = "image/jpeg, " +
            "image/png, " +
            "image/tiff, " +
            "image/heic, " +
            "image/heif, " +
            "image/svg+xml, " +
            "image/bmp, " +
            "image/gif, " +
            "application/zip, " +
            "application/zip-compressed, " +
            "application/x-zip-compressed, " +
            "application/vnd.rar, " +
            "application/x-rar, " +
            "application/x-rar-compressed, " +
            "application/x-7z-compressed, " +
            "application/x-compressed," +
            "application/pdf, " +
            "application/msword, " +
            "application/vnd.ms-excel, " +
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document, " +
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, " +
            "text/plain, " +
            "text/csv, " +
            "application/rtf, " +
            "application/vnd.oasis.opendocument.text, " +
            "application/vnd.oasis.opendocument.spreadsheet "
        RejectedFileMessage = reject_dict["rejected_all"]
    }
    const dropzoneOptions= {
        dictDefaultMessage: get_description(),
        acceptedFiles: acceptFile,
        dictInvalidFileType: RejectedFileMessage,
        dictCancelUpload: [dz_trans["cancelUpload"]],
        dictFileTooBig: dz_trans["fileTooBig"],
        dictCancelUploadConfirmation: [dz_trans["cancelUploadConfirm"]],
        dictMaxFilesExceeded:  [dz_trans["maxFilesExceeded"]],
        dictRemoveFile: [dz_trans["removeFile"]],
        maxFilesize: 100, // MB
        maxFiles: maxFiles,
        addRemoveLinks: addRemoveLinks,
        parallelUploads: 1,
        timeout: 10000000,
        init: function () {
            this.on("success", function (file, response) {
                file.id = response.id;
                file.previewElement.lastChild.style.display = null;
                let result = null;
                let message = "";
                if (response.duplicate && response.file_renamed) {
                    result = UploadResultsEnum.duplicate_renamed;
                    message = `${response.duplicate} ${response.file_renamed}`;
                } else if (response.renamed) {
                    result = UploadResultsEnum.renamed;
                    message = response.file_renamed;
                } else if (response.duplicate) {
                    result = UploadResultsEnum.duplicate;
                    message = response.duplicate;
                } else {
                    result = UploadResultsEnum.success;
                }
                if (result !== UploadResultsEnum.success) {
                    show_upload_successful_message(file, result, message);
                    console.log("success > " + file.name);
                } else {
                    show_upload_successful_message(file, result, message);
                }
                var submitButton = $(".btn-disable-when-running-upload");
                submitButton.prop('disabled', false); 
                submitButton.removeClass("disabled"); 
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
            this.on("addedfile", function (file) {
                //hack pro win10
                let exten=file.name.split('.').pop(); 
                if(file.type==="" && (exten==="rar" || exten==="7z"))
                    this.options.acceptedFiles="";
                else this.options.acceptedFiles=acceptFile;

                var submitButton = $(".btn-disable-when-running-upload");
                submitButton.prop('disabled', true);
                submitButton.addClass("disabled"); 
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
                show_upload_successful_message(file, UploadResultsEnum.error, response);
            }

            this.removeFile(file);

        },
        params: get_params(),
    };
    const uploader = document.querySelector('#my-awesome-dropzone');
    newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

Dropzone.autoDiscover = false;

const UploadResultsEnum = {
    success: 0,
    error: 2,
}

const show_upload_successful_message = (file, result = UploadResultsEnum.success, message = "") => {
    const collection = document.getElementsByClassName("message-container");
    if (collection.length > 0) {
        const message_container_element = collection[0];
        const alert_element = document.createElement("div");
        if (result === UploadResultsEnum.success) {
            alert_element.setAttribute("class", `alert alert-success alert-dismissible fade show app-alert-floating-import-pian`);
        } else {
            alert_element.setAttribute("class", `alert alert-danger alert-dismissible fade show app-alert-floating-import-pian`);
        }
        alert_element.setAttribute("role", "alert");
        if (result === UploadResultsEnum.success) {
            alert_element.textContent = [dz_trans["alertsImportPianUploadSuccesfull"]];
        } else {
            alert_element.textContent = [dz_trans["alertsImportPianUploadError"]] + " " + message;
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
    const csrfcookie = () => {
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
    let dropzoneOptions = {
        dictDefaultMessage: [dz_trans["description"]],
        acceptedFiles: ".csv, .CSV",
        dictInvalidFileType: [dz_trans["rejectedFileMessage"]],
        addRemoveLinks: true,
        dictCancelUpload: [dz_trans["cancelUpload"]],
        dictCancelUploadConfirmation: [dz_trans["cancelUploadConfirm"]],
        dictMaxFilesExceeded:  dz_trans["maxFilesExceeded"],
        dictRemoveFile: [dz_trans["removeFile"]],
        maxFilesize: 10, // MB
        maxFiles: 1,
        addRemoveLinks: false,
        parallelUploads: 1,
        timeout: 10000000,
        init: function () {
            this.on("success", function (file, response) {
                file.id = response.id
                file.previewElement.lastChild.style.display = null
                show_upload_successful_message(file, UploadResultsEnum.success);
                $("#my-awesome-dropzone").attr('style','display:none !important');
                $("#import-helptext").attr('style','display:none !important');
                $('#modal-pian-import-table').append(response);
                this.removeFile(file);
            });
            this.on("sending", function (file) {
                file.previewElement.lastChild.style.display = "none"
            });

        },
        error: function (file, response) {
            console.log(response);
            show_upload_successful_message(file, UploadResultsEnum.error, response);
            this.removeFile(file);

        },
    };
    const uploader = document.querySelector('#my-awesome-dropzone');
    const newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

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
    if (typeof object_id !== 'undefined') {
        return "Přiložte dokumentaci";
    }
    if (typeof file_id !== 'undefined') {
        return "Přiložte aktualizovaný soubor";
    }
    return "";
};
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
    if (currentLocation.includes("nahrat-soubor/pas/")) {
        acceptFile = "image/*"
        RejectedFileMessage = reject_dict["rejected_pas"] //pridat do message constants po merge AMCR-1 a otestovat
}
    else if (currentLocation.includes("nahrat-soubor/dokument/")) {
    acceptFile = "application/pdf"
    RejectedFileMessage = reject_dict["rejected_dokument"]
    }
    else {
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
    dictCancelUpload: "Zrušit nahrávání",
    dictCancelUploadConfirmation: "Naozaj chcete zrušit nahrávání?",
    dictRemoveFile: "Odstranit soubor",
    maxFilesize: 100, // MB
    maxFiles: maxFiles,
    init: function () {
        this.on("success", function (file, response) {
            file.id = response.id
            file.previewElement.lastChild.style.display = null
            if (response.duplicate) {
                alert(response.duplicate)
                console.log("success > " + file.name);

            }
        });
        this.on("removedfile", function (file) {
            if (file.id) {
                xhttp.open("POST", "/smazat-soubor/" + file.id);
                xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                xhttp.setRequestHeader('X-CSRFToken', csrfcookie());
                xhttp.send();
            }
        });
        this.on("sending", function (file) {
            file.previewElement.lastChild.style.display = "none"
        });
    },
    error: function (file, response) {
        console.log(response);
        alert(response)
        this.removeFile(file);

    },
    params: get_params(),
};
var uploader = document.querySelector('#my-awesome-dropzone');
var newDropzone = new Dropzone(uploader, dropzoneOptions);
console.log("Loaded");
};

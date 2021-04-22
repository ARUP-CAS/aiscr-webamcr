Dropzone.autoDiscover = false;
window.onload = function () {
    var dropzoneOptions = {
        dictDefaultMessage: 'Přiložte dokumentaci',
        dictInvalidFileType: "Nepodporovaný typ souboru",
        dictRemoveFile: "Odebrat",
        dictRemoveFileConfirmation: "Skutečně odebrat soubor?",
        acceptedFiles: "image/*," +
            "application/pdf," +
            ".csv," +
            ".txt," +
            "application/vnd.ms-excel," +
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document," +
            "application/docx," +
            "application/pdf," +
            "text/plain," +
            "application/msword," +
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        maxFilesize: 100, // MB
        addRemoveLinks: true,
        init: function () {
            this.on("success", function (file) {
                console.log("success > " + file.name);
            });
        },
        params: {'objectID': object_id}
    };
    var uploader = document.querySelector('#my-awesome-dropzone');
    var newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

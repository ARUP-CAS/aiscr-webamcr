Dropzone.autoDiscover = false;
window.onload = function () {
    var dropzoneOptions = {
        dictDefaultMessage: 'Přiložte dokumentaci.',
        dictInvalidFileType: "Nepodporovaný typ souboru.",
        acceptedFiles: "image/*," +
            ".zip," +
            ".ZIP," +
            ".rar," +
            ".RAR," +
            ".7z," +
            ".7Z," +
            "application/vnd.ms-excel," +
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document," +
            "application/docx," +
            "application/pdf," +
            "text/plain," +
            "application/msword," +
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet," +
            "application/vnd.oasis.opendocument.text," +
            "application/vnd.oasis.opendocument.spreadsheet",
        maxFilesize: 100, // MB
        init: function () {
            this.on("success", function (file, response) {
                console.log("success > " + file.name);
            });
        },
        error: function (file, response) {
            console.log(response);
            if (response.error) {
                alert(response.error)
            } else {
                alert(response)
            }
            this.removeFile(file);

        },
        params: { 'objectID': object_id }
    };
    var uploader = document.querySelector('#my-awesome-dropzone');
    var newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

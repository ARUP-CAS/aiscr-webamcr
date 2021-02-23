Dropzone.autoDiscover = false;
window.onload = function () {
    var dropzoneOptions = {
        dictDefaultMessage: 'Přiložte dokumentaci',
        dictInvalidFileType: "Nepodporovaný typ souboru",
        dictRemoveFile: "Odebrat",
        dictRemoveFileConfirmation: "Skutečně odebrat soubor?",
        acceptedFiles: "image/*,application/pdf,.csv,.txt,application/vnd.ms-excel",
        maxFilesize: 100, // MB
        addRemoveLinks: true,
        init: function () {
            this.on("success", function (file) {
                console.log("success > " + file.name);
            });
        },
        params: {'projektID': project_id}
    };
    var uploader = document.querySelector('#my-awesome-dropzone');
    var newDropzone = new Dropzone(uploader, dropzoneOptions);
    console.log("Loaded");
};

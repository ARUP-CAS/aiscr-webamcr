Dropzone.autoDiscover = false;
const get_params = () => {
    if (typeof object_id !== 'undefined') {
        return { 'objectID': object_id };
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

const ActionResultsEnum = {
    success: 0,
    duplicate: 1,
    reject: 2,
    error: 3,
    renamed: 4,
    duplicate_renamed: 4,
}

const ActionTypeEnum = {
    upload: 0,
    delete: 1,
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

const show_action_result_message = (file, result = ActionResultsEnum.success, message = "", action = ActionTypeEnum.upload) => {
    const collection = document.getElementsByClassName("message-container");
    if (collection.length > 0) {
        const sidebar_affected_class = check_sidebar_state() ? "app-alert-floating-file-upload-no-left-bar " : "";
        const message_container_element = collection[0];
        const alert_element = document.createElement("div");
        const sidebar_element_query = document.getElementsByClassName("app-sidebar-wrapper");
        const floating_class = sidebar_element_query.length > 0 ? "app-alert-floating-file-upload" : "app-alert-floating-file-upload-oznameni";
        const alert_common_classes = "alert alert-success alert-dismissible fade show app-alert-floating-file-upload";
        if (result === ActionResultsEnum.success) {
            const alert_status_class = "alert-success";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class}`);
        } else if (result === ActionResultsEnum.duplicate || result === ActionResultsEnum.renamed || result === ActionResultsEnum.duplicate_renamed) {
            const alert_status_class = "alert-warning";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class}`);
        } else if (result === ActionResultsEnum.reject || result === ActionResultsEnum.error) {
            const alert_status_class = "alert-danger";
            alert_element.setAttribute("class", `${alert_status_class} ${alert_common_classes} ${floating_class} ${sidebar_affected_class} ${message}`);
        }
        alert_element.setAttribute("role", "alert");
        if (action === ActionTypeEnum.upload) {
            if (result === ActionResultsEnum.success) {
                alert_element.textContent = `${dz_trans["alertsUploadSuccessfulPart1"]} ${file.name} ${dz_trans["alertsUploadSuccessfulPart2"]}`;
            } else if (result === ActionResultsEnum.duplicate || result === ActionResultsEnum.renamed || result === ActionResultsEnum.duplicate_renamed) {
                alert_element.textContent = message;
            } else if (result === ActionResultsEnum.reject) {
                alert_element.textContent = `${dz_trans["alertsUploadRejectPart1"]} ${file.name} ${dz_trans["alertsUploadRejectPart2"]}${message}`;
            } else if (result === ActionResultsEnum.error) {
                alert_element.textContent = `${dz_trans["alertsUploadErrorPart1"]} ${file.name} ${dz_trans["alertsUploadErrorPart2"]}${message}`;
            }
        } else if (action === ActionTypeEnum.delete) {
            if (result === ActionResultsEnum.success) {
                alert_element.textContent = `${dz_trans["alertsDeleteSuccessfulPart1"]} ${file.name} ${dz_trans["alertsDeleteSuccessfulPart2"]}`;
            } else if (result === ActionResultsEnum.error) {
                alert_element.textContent = `${dz_trans["alertsDeleteErrorPart1"]} ${file.name} ${dz_trans["alertsDeleteErrorPart2"]}`;
            }
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
            "application/x-7z-compressed,"+
            ".rar,"+
            ".7z"
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
            "application/vnd.oasis.opendocument.spreadsheet, "
            ".rar, "+
            ".7z "
        RejectedFileMessage = reject_dict["rejected_all"]
    }
    const dropzoneOptions= {
        dictDefaultMessage: get_description(),
        acceptedFiles: acceptFile,
        dictInvalidFileType: RejectedFileMessage,
        dictCancelUpload: dz_trans["cancelUpload"],
        dictFileTooBig: dz_trans["fileTooBig"],
        dictCancelUploadConfirmation: dz_trans["cancelUploadConfirm"],
        dictMaxFilesExceeded:  dz_trans["maxFilesExceeded"],
        dictRemoveFile: dz_trans["removeFile"],
        maxFilesize: 250, // MB
        maxFiles: maxFiles,
        addRemoveLinks: addRemoveLinks,
        parallelUploads: 1,
        timeout: 10000000,
        init: function () {
            this.on("success", function (file, response) {
                file.id = response.id;
                if (file.previewElement) {
                    const b = file.previewElement.querySelector("[data-dz-remove]");
                    if (b) b.innerText = dz_trans["removeFile"];
                }
                let result = null;
                let message = "";
                if (response.duplicate && response.file_renamed) {
                    result = ActionResultsEnum.duplicate_renamed;
                    message = `${response.duplicate} ${response.file_renamed}`;
                } else if (response.renamed) {
                    result = ActionResultsEnum.renamed;
                    message = response.file_renamed;
                } else if (response.duplicate) {
                    result = ActionResultsEnum.duplicate;
                    message = response.duplicate;
                } else {
                    result = ActionResultsEnum.success;
                }
                if (result !== ActionResultsEnum.success) {
                    show_action_result_message(file, result, message);
                } else {
                    show_action_result_message(file, result, message);
                }
            });
            this.on("addedfile", function (file) {
                toggleButtonsDisabled(true);
                updateRemoveLocks();
                const btn = file.previewElement.querySelector("[data-dz-remove]");

                //přepíše tlačítko delete
                if(btn){
                    const clone = btn.cloneNode(true);
                    btn.parentNode.replaceChild(clone, btn);

                    const setBtnText = () => { // nastavení textu tlačítka delete pod ikonou souboru
                        if (file.status === Dropzone.UPLOADING) {
                            clone.innerText = dz_trans["cancelUpload"];     // cancel během uploadu
                        } else if (file.id) {
                            clone.innerText = dz_trans["removeFile"];       // smazat ze serveru
                        } else {
                            clone.innerText = dz_trans["removeFile"];       // ještě bez id = jen odstranit z UI
                        }
                    };

                    setBtnText();
                                    
                    //vloží událost na tlačítko delete
                    clone.addEventListener("click", (e) => {
                        e.preventDefault();
                        e.stopPropagation();

                        if (file.status === Dropzone.UPLOADING) {  //mazání souboru při uploadu                            
                            this.cancelUpload(file);
                            this.removeFile(file); // odstraní z UI po zrušení                            
                            return;
                        }

                        if (!file.id) {  //mazání souboru ve frontě
                            this.removeFile(file);
                            return;
                        }

                        toggleAllLocked(true);
                        btn.style.pointerEvents = "none";
                        clone.innerText = dz_trans["removingFile"];

                        const xhttp = new XMLHttpRequest();
                        xhttp.open("POST", "/soubor/smazat-DZ/" + typ_vazby + "/" + object_id + "/" + file.id);
                        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
                        xhttp.setRequestHeader('X-CSRFToken', csrfcookie());
                        xhttp.onreadystatechange = () => {
                            if (xhttp.readyState === XMLHttpRequest.DONE) {
                                if (xhttp.status === 200) {
                                    show_action_result_message(file, ActionResultsEnum.success, "success", ActionTypeEnum.delete);
                                    //smaže ikonu až po fyzickém smazání na serveru
                                    this.removeFile(file);
                                } else {
                                    show_action_result_message(file, ActionResultsEnum.error, "error", ActionTypeEnum.delete);
                                    btn.style.pointerEvents = "auto";
                                    setBtnText();
                                }
                                toggleAllLocked(false);
                            }
                        };

                        xhttp.send("dropzone=true");
                    });
                }
            });
            this.on("processing", function (file) {
                 updateRemoveLocks(); 
            });
            this.on("queuecomplete", function () {
                 toggleButtonsDisabled(false);
                 updateRemoveLocks(); 
                 //po dokončení kompletního nahrání všech souborů, pro jistotu provedeme reload stránky, aby bylo jasné co se opravdu nahrálo a co ne
                setTimeout(() => {
                    location.reload();
                }, 1000);
            });
            this.on("sending", function (file, xhr /*, formData */) {
                // před odesláním: ještě povol cancel (tlačítko nezamykáme)
                file._awaitingServerResponseAfterUpload = false;
                updateRemoveLocks();

                // po doodeslání dat (progress 100%), ale před odpovědí serveru:
                xhr.upload.addEventListener("loadend", () => {
                    file._awaitingServerResponseAfterUpload = true;
                    updateRemoveLocks();   // teď zamkni tlačítko u tohoto uploadovaného souboru
                }, { once: true });
            });

            this.on("complete", function(file) {
                file._awaitingServerResponseAfterUpload = false;
                updateRemoveLocks();
            });

            this.on("removedfile", function() { updateRemoveLocks(); });

        },
        error: function (file, response) {
            console.log(response);
            if (Array.isArray(response) && response.includes('reject')) {
                show_action_result_message(file, ActionResultsEnum.reject, response);
            }
            else if (response.hasOwnProperty("error")) {
                show_action_result_message(file, ActionResultsEnum.error, response.error);
            } else {
                show_action_result_message(file, ActionResultsEnum.error, response);
            }

            this.removeFile(file);

        },
        params: get_params(),
    };
    const uploader = document.querySelector('#my-awesome-dropzone');
    newDropzone = new Dropzone(uploader, dropzoneOptions);
    //vloží do dropzone soubory, které už byly nahrány dříve
    let mock = [];
    if (mock_str) {
        try {
            mock = JSON.parse(mock_str);
        } catch(e) {            
            mock = [];
        }
    }
    mock.forEach(file => {
        let mockFile = {
            name: file.name,
            size: file.size,
            id: file.id, // Přidání ID pro mazání
            accepted: true
        };
        newDropzone.emit("addedfile", mockFile);        
        //stažení ikony souboru ze serveru
        newDropzone.emit("thumbnail", mockFile, "/soubor/stahnout-nahled-DZ/" + typ_vazby + "/" + object_id + "/" + file.id);
        mockFile.status = Dropzone.SUCCESS;
        mockFile.upload = { progress: 100, total: mockFile.size, bytesSent: mockFile.size };
        newDropzone.files.push(mockFile);

        if (mockFile.previewElement) {
            mockFile.previewElement.classList.add("dz-success", "dz-complete");
            mockFile.previewElement.classList.remove("dz-processing");
            const prog = mockFile.previewElement.querySelector(".dz-progress");
            if (prog) prog.style.display = "none"; 
        }
        toggleButtonsDisabled(false);
        updateRemoveLocks(); 
    });

    //zablokuje všechna tlačítka mazání
    function toggleFileRemoving(lock) {
        $("[data-dz-remove]").css({
            "pointer-events": lock ? "none" : "auto",
            "opacity": lock ? "0.4" : "1"
        });
    }

    //zablokuje jedno tlačítko mazání
    function toggleRemoveLockForFile(file, lock) {
        if (!file.previewElement) return;
        $(file.previewElement).find("[data-dz-remove]").css({
            "pointer-events": lock ? "none" : "auto",
            "opacity": lock ? "0.4" : "1"
        });
    }

    // blokuje mazání souborů podle zadaných podmínek
    function updateRemoveLocks() {
        // je teď nějaký soubor aktivně uploadovaný?
        const hasUploading = newDropzone.getUploadingFiles().length > 0; // používá interní statusy :contentReference[oaicite:0]{index=0}

        newDropzone.files.forEach(f => {
            // 1) soubory čekající ve frontě (ADDED/QUEUED): vždy povolit odstranit z fronty
            if (f.status === Dropzone.ADDED || f.status === Dropzone.QUEUED) {
            toggleRemoveLockForFile(f, false);
            return;
            }

            // 2) soubor uploadovaný: zamykáme jen když už je doodesláno a čeká se na odpověď
            if (f.status === Dropzone.UPLOADING) {
            toggleRemoveLockForFile(f, !!f._awaitingServerResponseAfterUpload);
            return;
            }

            // 3) už uploadnuté soubory (mají id): během uploadu jiného souboru je zamknout (aby nešel server delete)
            if (f.id && hasUploading) {
            toggleRemoveLockForFile(f, true);
            return;
            }

            // 4) jinak povolit
            toggleRemoveLockForFile(f, false);
        });
    }

    //zablokuje vše - nahrávání,  mazání a tlačítka
    function toggleAllLocked(lock) {
        toggleButtonsDisabled(lock)
        lock ? newDropzone.disable() : newDropzone.enable();
        toggleFileRemoving(lock);
    }
    //zablokuje tlačítka
    function toggleButtonsDisabled(lock) {
        const submitButton = $(".btn-disable-when-running-upload");
        submitButton
            .prop("disabled", lock)
            .toggleClass("disabled", lock);
    }

};

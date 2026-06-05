var successFunction = function(settings, response) {
    const $sel = $('#id_vedouci_modal');
    const val = String(response.value);
    const selected = [].concat($sel.val() || []).map(String);
    $sel.append(new Option(response.text, response.value, true, true));
    if (selected.indexOf(val) === -1) {
      selected.push(val);
    }
    $sel.val(selected).trigger('change');

    $("#submit-btn").prop("disabled", false);
    $("#submit-btn").siblings('button').prop("disabled", false);
    $("#loader-spinner").hide();

    $(settings.modalIDD).modal("hide");
  };
  window.addEventListener("modalLoaded", function() {
    var options = Object.assign(Object.create(defaults), {
      modalID: "modal-osoba-form",
      formURL: heslar_url,
      formID: "create-osoba-form",
      modalContent: ".modal-content",
      modalForm: ".modal-content osoba-form",
      modalFormID: "#create-osoba-form",
      modalIDD : "#modal-osoba-form",
      successFunc: successFunction,
      firstModalID: "#modal-form",
      secondModal: modal,
    })
    new Modal(options, "create-vedouci-id_vedouci_modal");  
  });
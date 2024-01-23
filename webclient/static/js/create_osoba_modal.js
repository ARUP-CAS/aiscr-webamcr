var successFunction = function(settings, response) {
    let dropdown = document.getElementById('id_vedouci_modal');
    let newOption = document.createElement('option');
    newOption.text = response.text;
    newOption.value = response.value;

    dropdown.add(newOption);
    
    $('#id_vedouci_modal').selectpicker('refresh');
    $('#id_vedouci_modal').selectpicker('val', response.value);
    dropdown.value = response.value;
    $(settings.modalIDD).modal("hide");
  };
  console.log(document.getElementById('id_vedouci_modal'))
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
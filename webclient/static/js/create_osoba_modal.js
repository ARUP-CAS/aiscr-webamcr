var successFunction = function(settings, response) {
    // Pole "vedouci" je Select2 (AutocompleteModelSelect2Multiple), ne bootstrap-select.
    // Nová osoba se přidává ke STÁVAJÍCÍMU výběru – čteme aktuální val() a nastavíme
    // sjednocení (původní + nová). Pouhý append + change tady původní hodnoty ztrácí,
    // protože jde o modal-v-modalu (edit modal se při otevření osoba dialogu skryje a
    // poté znovu zobrazí), viz #3957.
    const $sel = $('#id_vedouci_modal');
    const val = String(response.value);
    const selected = ($sel.val() || []).map(String);
    $sel.append(new Option(response.text, response.value, true, true));
    if (selected.indexOf(val) === -1) {
      selected.push(val);
    }
    $sel.val(selected).trigger('change');

    // Osoba-formulář nemá vlastní #submit-btn, takže isFormValid() při jeho odeslání
    // zakázal #submit-btn editačního modalu a po úspěchu ho už nikdo nepovolil zpět
    // (tlačítko Uložit zůstalo zablokované a modal nešel zavřít). Vrátíme ho do funkčního
    // stavu, viz #3957.
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
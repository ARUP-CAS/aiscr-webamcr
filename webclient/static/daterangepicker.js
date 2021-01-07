// setting locale to the daterangepicker
moment.locale('cs');
$('input[name="planovane_zahajeni"]').daterangepicker({
    "locale": {
        "applyLabel": "Vybrat odhad začátku pracíaaa",
        "cancelLabel": "Zrušit"
    },
    format: 'dd/mm/yyyy'
});

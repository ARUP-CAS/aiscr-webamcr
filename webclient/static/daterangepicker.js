// setting locale to the daterangepicker
moment.locale('cs');
$('input[name="planovane_zahajeni"]').daterangepicker({
    autoUpdateInput: false,
    locale: {
        cancelLabel: "Zrušit",
        applyLabel: "Vybrat odhad začátku prací"
    },

});

$('input[name="planovane_zahajeni"]').on('apply.daterangepicker', function(ev, picker) {
    $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
});

$('input[name="planovane_zahajeni"]').on('cancel.daterangepicker', function(ev, picker) {
    $(this).val('');
});

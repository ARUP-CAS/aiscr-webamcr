// setting locale to the daterangepicker
moment.locale('cs');
var load_daterangepicker = function (div_id) {
    $('input[name="planovane_zahajeni"]').daterangepicker({
        parentEl: div_id,
        autoUpdateInput: false,
        locale: {
            cancelLabel: drp_translations['cancelLabel'],  // "Zrušit"
            applyLabel: drp_translations['applyLabel'],  // "Vybrat odhad začátku prací"
            format: 'D.M.YYYY'
        },
    });
}

$('input[name="planovane_zahajeni"]').on('apply.daterangepicker', function (ev, picker) {
    $(this).val(picker.startDate.format('D.M.YYYY') + ' - ' + picker.endDate.format('D.M.YYYY'));
});

$('input[name="planovane_zahajeni"]').on('cancel.daterangepicker', function (ev, picker) {
    $(this).val('');
});

// setting locale to the daterangepicker
moment.locale('cs');
var load_daterangepicker = function(div_id){
$('input[name="planovane_zahajeni"]').daterangepicker({
    parentEl: div_id,
    autoUpdateInput: false,
    locale: {
        cancelLabel: "Zrušit",
        applyLabel: "Vybrat odhad začátku prací"
    },
});
}

$('input[name="planovane_zahajeni"]').on('apply.daterangepicker', function (ev, picker) {
    $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
});

$('input[name="planovane_zahajeni"]').on('cancel.daterangepicker', function (ev, picker) {
    $(this).val('');
});

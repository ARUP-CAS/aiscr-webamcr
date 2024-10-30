$(document).ready(function () {
  $('form.submit-spinner').on('submit', function() {
    const submitButton = $(this).find('button[type=submit]');
    submitButton.prop('disabled', true); // Zablokuje tlačítko
    submitButton.find('.spinner-border').show(); // Zobrazí spinner
    submitButton.siblings('a').addClass("disabled")
    $(".submit-remove").hide();
  });
})
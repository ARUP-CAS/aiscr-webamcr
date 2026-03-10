// Disable scrolling when datepicker is opened
// Prevents datepicker from moving/jumping when user scrolls while picker is visible

$(document).ready(function () {
    const $appWrapper = $('#app-wrapper');
    let originalOverflowY = 'auto';

    // Listen for datepicker show event
    $(document).on('show.datepicker', function (e) {
        if ($appWrapper.length) {
            // Only store the original overflow-y once, not on every show event
            if (!$appWrapper.data('datepicker-scroll-fix-active')) {
                originalOverflowY = $appWrapper.css('overflow-y');
                $appWrapper.data('datepicker-scroll-fix-active', true);
            }
            $appWrapper.css('overflow-y', 'hidden');
        }
    });

    // Listen for datepicker hide event
    $(document).on('hide.datepicker', function (e) {
        if ($appWrapper.length) {
            $appWrapper.css('overflow-y', originalOverflowY);
            $appWrapper.data('datepicker-scroll-fix-active', false);
        }
    });
});



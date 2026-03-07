function createMessage(tag, message, button = 'False', append = 'True', alert = 'True') {
    let msg;
    if (button === 'True') {
        msg = `<div class="alert alert-${tag} alert-dismissible fade show app-alert-floating" role="alert">
        <button id="prolong_btn" type="button" class="btn btn-prolong">${message}</button>
        <button aria-label="Close" class="btn-close" data-bs-dismiss="alert" type="button"></button></div>`;
    } else {
        msg = `<div class="alert alert-${tag} alert-dismissible fade show app-alert-floating" role="alert">
            ${message}
            <button aria-label="Close" class="btn-close" data-bs-dismiss="alert" type="button"></button></div>`;
    }

    if (append === 'True') {
        const $msg = $(msg);
        $('.message-container').append($msg);
    
        if (alert === 'True') {
            $msg.delay(5000).slideUp(200, function () {
                $(this).alert('close');
            });
        }
    } else {
        return msg;
    }
}

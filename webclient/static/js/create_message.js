function createMessage (tag, message, button='False', append='True', alert='True') {
    if (button === 'True') {
      msg = `<div class="alert alert-${tag} alert-dismissible fade show app-alert-floating" role="alert">
        <button id="prolong_btn" type="button" class="btn btn-prolong">${message}</button>
        <button aria-label="Close" class="close" data-dismiss="alert" type="button">
        <span aria-hidden="true">&times;</span></button></div>`;      
    } else {
    msg = `<div class="alert alert-${tag} alert-dismissible fade show app-alert-floating" role="alert">
            ${message}
            <button aria-label="Close" class="close" data-dismiss="alert" type="button">
            <span aria-hidden="true">&times;</span></button></div>`;
        }
  
    if (append === 'True'){
        $('.message-container').append(msg);
        if (alert === 'True'){
            $(".app-alert-floating").delay(5000).slideUp(200, function() {
                $(this).alert('close');
            });
        }
    } else {
        return msg
    }  
}
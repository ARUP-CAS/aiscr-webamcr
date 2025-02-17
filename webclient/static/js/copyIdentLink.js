
function copy_ident_link(ident) {
    const link = window.location.origin + '/id/' + ident;
    navigator.clipboard.writeText(link);
}
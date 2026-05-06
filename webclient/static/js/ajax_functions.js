get_vychozi_hodnota_podrazeneho = function (nadrazeneID, podrazeneID, start_url) {
    $(nadrazeneID).on("changed.bs.select",
        function (e, clickedIndex, newValue, oldValue) {
            const xhttp = new XMLHttpRequest();
            xhttp.onload = function () {
                if (this.status === 200) {
                    let array = []
                    for (let i = 0; i < JSON.parse(this.responseText).length; i++) {
                        array = array.concat(JSON.parse(this.responseText)[i].id)
                    }
                    $(podrazeneID).selectpicker('val', array.map(String));
                    $(podrazeneID).selectpicker('refresh');
                } else {
                    $(podrazeneID).selectpicker('val', "");
                    $(podrazeneID).selectpicker('refresh');
                }
            }
            const next_url = start_url + this.value
            xhttp.open("GET", next_url);
            xhttp.send();
        });
}

get_vychozi_licence = function (organizaceID, licenceID, start_url) {
    $(organizaceID).on("changed.bs.select",
        function (e, clickedIndex, newValue, oldValue) {
            const xhttp = new XMLHttpRequest();
            xhttp.onload = function () {
                // Místo refresh se používá destroy+reinit, aby se předešlo chybě bootstrap-select 1.14.0-beta3,
                // kdy buildData() přidává data do main.data místo jejich nahrazení (vizuálně se hodnoty řetězí).
                if (this.status === 200) {
                    const data = JSON.parse(this.responseText)
                    $(licenceID).val(String(data.licence));
                }
                else {
                    $(licenceID).val("");
                }
                $(licenceID).selectpicker('destroy').selectpicker();
            }
            const next_url = start_url + this.value
            xhttp.open("GET", next_url);
            xhttp.send();
        });
}
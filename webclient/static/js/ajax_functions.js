get_vychozi_hodnota_podrazeneho = function (nadrazeneID, podrazeneID, start_url) {
    $(nadrazeneID).on("changed.bs.select",
        function (e, clickedIndex, newValue, oldValue) {
            const xhttp = new XMLHttpRequest();
            xhttp.onload = function () {
                // Místo refresh se používá destroy+reinit, aby se předešlo chybě bootstrap-select
                // 1.14.0-beta3, kdy buildData() přidává data do main.data místo jejich nahrazení
                // (u multiselectu se po refresh duplikují položky v nabídce, viz #3957 / #3917).
                if (this.status === 200) {
                    const data = JSON.parse(this.responseText)
                    let array = []
                    for (let i = 0; i < data.length; i++) {
                        array = array.concat(data[i].id)
                    }
                    $(podrazeneID).val(array.map(String));
                } else {
                    $(podrazeneID).val([]);
                }
                $(podrazeneID).selectpicker('destroy').selectpicker();
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
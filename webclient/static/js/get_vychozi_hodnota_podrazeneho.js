get_vychozi_hodnota_podrazeneho = function (nadrazeneID, podrazeneID, start_url) {
    $(nadrazeneID).on("changed.bs.select", 
      function(e, clickedIndex, newValue, oldValue) {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
      if (this.status == 200){
        $(podrazeneID).selectpicker('val', JSON.parse(this.responseText).id);
        $(podrazeneID).selectpicker('refresh');
      }
      else {
        $(podrazeneID).selectpicker('val', "");
        $(podrazeneID).selectpicker('refresh');
      }
    }
    url = start_url + this.value
    console.log(url)
    xhttp.open("GET", url);
    xhttp.send();
    });
    }
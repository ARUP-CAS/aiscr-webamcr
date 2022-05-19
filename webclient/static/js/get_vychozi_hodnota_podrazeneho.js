get_vychozi_hodnota_podrazeneho = function (nadrazeneID, podrazeneID, start_url) {
    $(nadrazeneID).on("changed.bs.select", 
      function(e, clickedIndex, newValue, oldValue) {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
      if (this.status == 200){
        var array = []
        for (var i = 0; i < JSON.parse(this.responseText).length; i++) {
          array = array.concat(JSON.parse(this.responseText)[i].id) 
        }
        console.log(array)
        $(podrazeneID).selectpicker('val', array);
        $(podrazeneID).selectpicker('refresh');
      }
      else {
        $(podrazeneID).selectpicker('val', "");
        $(podrazeneID).selectpicker('refresh');
      }
    }
    next_url = start_url + this.value
    xhttp.open("GET", next_url);
    xhttp.send();
    });
    }
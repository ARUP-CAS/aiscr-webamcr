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

    get_vychozi_licence = function (organizaceID, licenceID, start_url) {
        $(organizaceID).on("changed.bs.select", 
          function(e, clickedIndex, newValue, oldValue) {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
          if (this.status == 200){
            let data=JSON.parse(this.responseText)

            $(licenceID).selectpicker('val', data.licence);
            $(licenceID).selectpicker('refresh');
          }
          else {
            $(licenceID).selectpicker('val', "");
            $(licenceID).selectpicker('refresh');
          }
        }
        next_url = start_url + this.value
        xhttp.open("GET", next_url);
        xhttp.send();
        });
        }
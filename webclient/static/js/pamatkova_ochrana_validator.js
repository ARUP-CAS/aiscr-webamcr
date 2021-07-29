var pamatkova_ochrana = document.getElementById("id_kulturni_pamatka");
var pamatka_cislo = document.getElementById("id_kulturni_pamatka_cislo").value
var pamatka_popis = document.getElementById("id_kulturni_pamatka_popis").value
document.addEventListener('DOMContentLoaded', checkPamatkovaOchrana);
pamatkova_ochrana.addEventListener("change", checkPamatkovaOchrana);

function checkPamatkovaOchrana() {
    console.log(pamatkova_ochrana.value);
    if (pamatkova_ochrana.value === "175") {
        disableFields();
    }
    else {
        enableFields();
    }
};

function disableFields() {
    pamatka_cislo = document.getElementById("id_kulturni_pamatka_cislo").value;
    document.getElementById("id_kulturni_pamatka_cislo").value = "";
    pamatka_popis = document.getElementById("id_kulturni_pamatka_popis").value;
    document.getElementById("id_kulturni_pamatka_popis").value = "";
    document.getElementById("id_kulturni_pamatka_cislo").disabled = true;
    document.getElementById("id_kulturni_pamatka_popis").disabled = true;
    document.getElementById("id_kulturni_pamatka_cislo").required = false;
    document.getElementById("id_kulturni_pamatka_popis").required = false;
};

function enableFields() {
    document.getElementById("id_kulturni_pamatka_cislo").value = pamatka_cislo;
    document.getElementById("id_kulturni_pamatka_popis").value = pamatka_popis;
    document.getElementById("id_kulturni_pamatka_cislo").disabled = false;
    document.getElementById("id_kulturni_pamatka_popis").disabled = false;
    document.getElementById("id_kulturni_pamatka_cislo").required = true;
    document.getElementById("id_kulturni_pamatka_popis").required = true;
};
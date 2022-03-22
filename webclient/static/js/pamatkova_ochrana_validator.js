element_pamat_cislo = document.getElementById("id_kulturni_pamatka_cislo")
label_pamat_cislo = element_pamat_cislo.parentElement.parentElement.getElementsByTagName("label")[0]
element_pamat_popis = document.getElementById("id_kulturni_pamatka_popis")
label_pamat_popis = element_pamat_popis.parentElement.parentElement.getElementsByTagName("label")[0]

var pamatkova_ochrana = document.getElementById("id_kulturni_pamatka");
var pamatka_cislo = element_pamat_cislo.value
var pamatka_popis = element_pamat_popis.value
document.addEventListener('DOMContentLoaded', checkPamatkovaOchrana);
pamatkova_ochrana.addEventListener("change", checkPamatkovaOchrana);

function checkPamatkovaOchrana() {
    console.log(pamatkova_ochrana.value);
    if (pamatkova_ochrana.value === "175" || pamatkova_ochrana.value === "") {
        disableFields();
    }
    else {
        enableFields();
    }
};


function disableFields() {
    pamatka_cislo = element_pamat_cislo.value;
    element_pamat_cislo.value = "";
    pamatka_popis = element_pamat_popis.value;
    element_pamat_popis.value = "";
    element_pamat_cislo.disabled = true;
    element_pamat_popis.disabled = true;
    element_pamat_cislo.required = false;
    element_pamat_popis.required = false;
    label_pamat_cislo.getElementsByTagName("span")[0].remove()
    label_pamat_popis.getElementsByTagName("span")[0].remove()

};

function enableFields() {
    element_pamat_cislo.value = pamatka_cislo;
    element_pamat_popis.value = pamatka_popis;
    element_pamat_cislo.disabled = false;
    element_pamat_popis.disabled = false;
    if (pamatkova_ochrana.required == true) {
        element_pamat_cislo.required = true;
        label_pamat_cislo.classList.add("requiredField");
        label_pamat_cislo.insertAdjacentHTML("beforeend",'<span class="asteriskField">*</span>')
        element_pamat_popis.required = true;
        label_pamat_popis.classList.add("requiredField");
        label_pamat_popis.insertAdjacentHTML("beforeend",'<span class="asteriskField">*</span>')
    };
};
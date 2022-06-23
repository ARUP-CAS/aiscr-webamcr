var global_fixed_precision = {
    wgs84: 7,
    jtsk: 2
}



function amcr_static_coordinate_precision_wgs84(text) {
    if (Array.isArray(text)) {
        return [
            amcr_static_coordinate_precision(text[0], global_fixed_precision.wgs84),
            amcr_static_coordinate_precision(text[1], global_fixed_precision.wgs84)
        ];
    } else {
        return amcr_static_coordinate_precision(text, global_fixed_precision.wgs84)
    }

}
function amcr_static_coordinate_precision_jtsk(text, switchQuadrant) {
    var scale = 1.0;
    if (switchQuadrant) {
        scale = -1.0;
    }

    if (Array.isArray(text)) {
        return [
            (scale * amcr_static_coordinate_precision(text[0], global_fixed_precision.jtsk)).toFixed(global_fixed_precision.jtsk),
            (scale * amcr_static_coordinate_precision(text[1], global_fixed_precision.jtsk)).toFixed(global_fixed_precision.jtsk)
        ];
    } else {
        return (scale * amcr_static_coordinate_precision(text, global_fixed_precision.wgs84)).toFixed(global_fixed_precision.jtsk)
    }
}

function amcr_static_coordinate_precision(text, in_precison) {
    var nn = Math.pow(10, in_precison) * 1.0;
    var num = Math.round(text * nn) / nn;
    return (num).toFixed(in_precison)
}

function amcr_static_geom_precision_wgs84(text) {
    return amcr_static_geom_precision(text, global_fixed_precision.wgs84)
}

function amcr_static_geom_precision_jtsk(text) {
    return amcr_static_geom_precision(text, global_fixed_precision.jtsk)
}

function amcr_static_geom_precision(in_text, in_precison) {
    var text = ""; //local copy of text
    var loc_p = -1; //local precision
    var loc_buffer = "";

    var empty_buffer = () => {
        if (loc_buffer.length > 0) {
            var nn = Math.pow(10, in_precison) * 1.0;
            var num = Math.round(loc_buffer * nn) / nn;
            /*if(num.lastIndexOf(".")==-1){
                num=num+".";
                //console.log(".")
            }
            while(num.lastIndexOf(".")+in_precison+1>num.length){
                num=num+"0";
                //console.log("0")
            }*/
            text = text + (num).toFixed(in_precison);
            loc_buffer = "";
        }

    }
    //console.log("---------------"+in_text)
    for (const x of in_text.toString()) {
        //console.log(x+" "+"0123456789.".indexOf(x))
        if ("0123456789.".indexOf(x) > -1) {
            if (loc_p == -1) {
                
                loc_buffer = loc_buffer + x;
                if (x == ".") {
                    loc_p = 0;
                }
                //console.log("1: "+x+" "+loc_p);
            } else if (loc_p <= in_precison) {
                //console.log("2: "+x+" "+loc_p);
                loc_p = ++loc_p;
                loc_buffer = loc_buffer + x;
            } else {
                //console.log("3: "+x+" "+loc_p);
            }
        } else {
            loc_p = -1
            empty_buffer();
            text = text + x;
        }
    }
    empty_buffer();
    return text;
};

   //formatCoordinates("oooo123.456789 ooo 256.78988 8999.999",2)

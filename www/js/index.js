function main(){
    autoreplaceall()
    $("#clicktrigger").on("click", function() {
        $("#file").trigger("click");
    });

    $("#file").change(function (){
        modal("loading")
        sendfile()
     });
}


function sendfile()
{
    var data = new FormData();
    data.append("file", $("#file").prop("files")[0])
    loading("Transfert du fichier, merci de patienter")
    $.ajax({
        type: 'POST',
        processData: false, // important
        contentType: false, // important
        data: data,
        dataType: 'text',
        url: "/upload/"+$("#CONST_PATH").html(),
        // in PHP you can call and process file in the same way as if it was submitted from a form:
        // $_FILES['input_file_name']
        success: function(jsonData){
            modalClose("loading")
            window.location.reload()
        },
        error : function(_a, _b, _c)
        {
            modalClose("loading")
            error("Impossible d'envoyer le fichier", _a.responseText)
        }
    });
}

GB=1024*1024*1024
MB=1024*1024
KB=1024

MIME={

}


function min(x,y){ return x>y?x:y }

function autoreplace_boundtext(text){
    max_size=13
    nline=3
    text = text.length>nline*max_size ? text.substr(0,max_size*nline-3)+"...": text
    out=""
    for(var i=0; i<nline; i++)
    {
        line=min(text.length, text.substr(0, max_size))
        text=text.substr(max_size)
        out+=line+"<br>"
    }
    return out
}

function autoreplace_size(value){
    if(value>=GB) return (value/GB).toFixed(1)+" Gio"
    if(value>=MB) return (value/MB).toFixed(1)+" Mio"
    if(value>=KB) return (value/KB).toFixed(1)+" Kio"
    return value+" o"
}


function autoreplace_mime(mime) {
    if(mime.startsWith("audio/")) return "audiotrack"
    if(mime.startsWith("video/")) return "movie"
    if(mime.startsWith("image/")) return "photo"
    if(mime.startsWith("text/")) return "format_align_justify"
    if(mime=="application/pdf") return "picture_as_pdf"

    if( mime in ["application/zip", "application/x-tar", "application/x-rar-compressed",
                "application/x-bzip", "application/x-bzip2", "application/x-tar+gzip", "application/gzip"]) return "archive"
    return "insert_drive_file"
}

function autoreplace_menupath(path)
{
    path=path.split('/')
    acc="/browse/"
    out=[]
    for(p in path){
        if(path[p]!="")
        {
            out.push($('<li><a href="'+acc+'" class="menu">/</a></li>'))
            acc+=path[p]
            out.push($('<li><a href="'+acc+'" class="menu">'+path[p]+'</a></li>'))
        }
    }
    out.push($('<li><a href="'+acc+'" class="menu">/</a></li>'))
    return out
}



function new_file()
{
    modalClose("add_file_dir")
    $("#file").click()

}

function new_dir()
{
    modalClose("add_file_dir")
   modal("add_dir")

}



function on_new()
{
   modal("add_file_dir")
}
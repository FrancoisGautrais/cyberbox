
current_edit_name=""
current_path=""

_sort_field=null
_sort_order=null
function _cmp(a,b)
{
    a=a.attributes["data-"+_sort_field].value
    b=b.attributes["data-"+_sort_field].value
    if(_sort_field!="name"){
        a=parseFloat(a)
        b=parseFloat(b)
        console.log(a+" "+b)
        return (_sort_order=="dec")?(a<b):(a>b)
    }
    return (_sort_order=="dec")?(a.toLowerCase()<b.toLowerCase()):(a.toLowerCase()>b.toLowerCase())
}

function sort(field, order) {
    data.user.sort=_sort_field=field
    data.user.order=_sort_order=order
    list=[]
    llist=$(".sortable").each(function(a,b){list.push(b)})
    root=llist.parent()
    llist.remove()
    list.sort(_cmp)
    for(var i in list){
        root.append($(list[i]))
    }

}

function main(){
    autoreplaceall()
    $("#clicktrigger").on("click", function() {
        $("#file").trigger("click");
    });

    $("#file").change(function (){
        modal("loading")
        sendfile()
     });

     current_path=$("#CONST_PATH").html()
}

function confirm_modify(){
    x=$("#edit_can_read").is(":checked")?"r":""
    x+=$("#edit_can_write").is(":checked")?"w":""
    x+=$("#edit_can_exec").is(":checked")?"x":""
    x+=$("#edit_is_hidden").is(":checked")?"h":""
    data={
        "attrs" : x
    }
    modal("loading")
    $.ajax({
            type: 'POST',
            processData: false, // important
            contentType: false, // important
            url: "/file/"+current_path+current_edit_name,
            data: JSON.stringify(data),
            headers : {
                "Content-Type": "application/json"
            },
            success: function(jsonData){
                modalClose("loading")
                modalClose("edit_file")
                window.location.reload()
            },
            error : function(_a, _b, _c)
            {
                modalClose("loading")
                error("Impossible de modifier '"+current_edit_name+"'", _a.responseText)
            }
     });


}

function confirm_delete()
{
    confirm("Êtes-vous sûr ?", "Voulez vous vraiment supprimer '"+current_edit_name+"'", function(){
            modal("loading")
            $.ajax({
                type: 'GET',
                processData: false, // important
                contentType: false, // important
                url: "/delete/"+current_path+"/"+current_edit_name,

                success: function(jsonData){
                    modalClose("loading")
                    modalClose("edit_file")
                    window.location.reload()
                },
                error : function(_a, _b, _c)
                {
                    modalClose("loading")
                    error("Impossible de supprimer '"+current_edit_name+"'", _a.responseText)
                }
            });
        })
}

function _edit_file(name, data)
{
    modalClose("loading")
    modal("edit_file")
    $("#edit_name").val(data["name"])
    $("#edit_can_read").prop('checked', data["attrs"].search("r")>=0);
    $("#edit_can_write").prop('checked', data["attrs"].search("w")>=0);
    $("#edit_can_exec").prop('checked', data["attrs"].search("x")>=0);
    $("#edit_is_hidden").prop('checked', data["attrs"].search("h")>=0);
    M.updateTextFields();
}

function edit_file(name)
{
    current_edit_name=name
    loading("Chargement")
    $.ajax({
        type: 'GET',
        processData: false, // important
        contentType: false, // important
        dataType: 'json',
        url: "/file"+$("#CONST_PATH").html()+"/"+name,

        success: function(jsonData){
            modalClose("loading")
            _edit_file(name, jsonData)
        },
        error : function(_a, _b, _c)
        {
            modalClose("loading")
            error("Impossible de récupérer les données", _a.responseText)
        }
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
function padd(x, n=2) {
    x=""+x
    while(x.length<n) x="0"+x
    return x
}
function autoreplace_date(text){
    timestamp=parseFloat(text)
    date = new Date(timestamp * 1000)
    return padd(date.getDate())+"/"+padd(date.getMonth()+1)+"/"+date.getFullYear()+" "+padd(date.getHours())+":"+padd(date.getMinutes())
}

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
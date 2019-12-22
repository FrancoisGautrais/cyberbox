$(document).ready(function(){
    autoreplaceall()
});

GB=1024*1024*1024
MB=1024*1024
KB=1024

MIME={

}


function replaceSize(value){
    if(value>=GB) return (value/GB).toFixed(1)+" Gio"
    if(value>=MB) return (value/MB).toFixed(1)+" Mio"
    if(value>=KB) return (value/KB).toFixed(1)+" Mio"
    return value+" o"
}
m=null
function replaceMime(mime) {
    if(mime.startsWith("audio/")) return "audiotrack"
    if(mime.startsWith("video/")) return "movie"
    if(mime.startsWith("image/")) return "photo"
    if(mime.startsWith("text/")) return "format_align_justify"
    if(mime=="application/pdf") return "picture_as_pdf"

    if( mime in ["application/zip", "application/x-tar", "application/x-rar-compressed",
                "application/x-bzip", "application/x-bzip2", "application/x-tar+gzip", "application/gzip"]) return "archive"
    return "insert_drive_file"
}

function handleReplace(el, type, value){
    switch (type) {
        case "size": return el.replaceWith(replaceSize(parseInt(value)))
        case "mime": return el.replaceWith(replaceMime(value))
        case "menupath":
            x=handleMenu(value)
            for( i in x){
            console.log(x[i])
                $(el).parent().append(x[i])
            }
            //el.remove()
            return
    }
}

function handleMenu(path)
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

function autoreplaceall()
{
    $(".autoreplace").each(function(index, el){
        handleReplace(el, el.attributes["data-type"].value, el.attributes["data-value"].value)
    })
}
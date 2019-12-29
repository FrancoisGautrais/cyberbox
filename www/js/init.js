


var MODALS={}

function modal(s, fct=null, args=null)
{
    obj = MODALS[s]
    obj.open()
    if(fct!=null) {
        fct(args)
    }
}

function modalClose(s, fct=null, args=null)
{
    obj = MODALS[s]
    obj.close()
    if(fct!=null) {
        fct(args)
    }
}

function _confirmClose(after)
{
    modalClose("confirm")

}

function confirm(title, text, onYes, onNo=null)
{
    $("#confirm-title").html(title)
    $("#confirm-text").html(text)
    $("#confirm-no").off("click")
    $("#confirm-no").on("click", function(){
        modalClose("confirm")
        if(onNo) onNo()
     })

    $("#confirm-yes").off("click")
    $("#confirm-yes").on("click", function(){
        modalClose("confirm")
        if(onYes) onYes()
     })
     modal("confirm")
}

function loading(text)
{
    $("#loading-text").html(text)
    modal("loading")
}

function error(title, text)
{
    $("#error-title").html(title)
    $("#error-text").html(text)
    modal("error")
}

function autoreplaceall()
{
    console.log($(".autoreplace"))
    $(".autoreplace").each(function(index, el){
        el=$(el)
        name="autoreplace_"+el.attr("data-type")
        ret=window[name](el.attr("data-value"), el)
        if(Array.isArray(ret))
        {
            for(var i = ret.length-1; i>=0; i--){
                el.after(ret[i])
            }
        }
        else{
            el.after(ret)
        }
        el.remove()
    })
}

document.addEventListener('DOMContentLoaded', function() {
    var elems = document.querySelectorAll('.sidenav');
    var instances = M.Sidenav.init(elems, {});
    M.updateTextFields();
    $(function() {
            M.updateTextFields();
    });
});

function url(x){window.location.href=x}

$(document).ready(function(){
    autoreplaceall()
    $('select').formSelect();

    $('.modal').modal();
    $('.modal').each(function(i, obj){
        MODALS[obj.attributes["id"].value]=M.Modal.getInstance(obj)
    })
    $('.dropdown-trigger').dropdown();

    if (typeof main === "function") {
        main();
    }
})
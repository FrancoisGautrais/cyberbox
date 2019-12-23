$(document).ready(function(){
    $('select').formSelect();

    $("#select_display").val($("#DISPLAY").html());
    $('select').formSelect();


});

document.addEventListener('DOMContentLoaded', function() {
    var elems = document.querySelectorAll('.sidenav');
    var instances = M.Sidenav.init(elems, {});
    M.updateTextFields();
    $(function() {
        M.updateTextFields();
    });
});

function on_erease()
{
    $.ajax({
        type: 'POST',
        processData: false, // important
        contentType: false, // important
        data: "",
        url: "/user/delete",
        // in PHP you can call and process file in the same way as if it was submitted from a form:
        // $_FILES['input_file_name']
        success: function(jsonData){
            window.location.reload()
        }
    });
}

function on_save()
{
    $.ajax({
        type: 'POST',
        processData: false, // important
        contentType: false, // important
        data: JSON.stringify({
            display: $("#select_display").val()
        }),
        headers: {
            "Content-Type": "application/json"
        },
        url: "/user/modify",
        // in PHP you can call and process file in the same way as if it was submitted from a form:
        // $_FILES['input_file_name']
        success: function(jsonData){
            window.location.reload()
        }
    });
}
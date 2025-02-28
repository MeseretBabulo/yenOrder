$( document ).ready(function() {

    $("#partner_relationship_selection").change(function () {
        var selected_option = $('#partner_relationship_selection').val();
        if (selected_option && selected_option != 'self'){
            $("input[name='representative_firstname']").parent().parent().parent().removeClass('d-none')
            $("input[name='representative_firstname']").attr("required", "true");
            $("input[name='representative_lastname']").parent().parent().parent().removeClass('d-none')
            $("input[name='representative_lastname']").attr("required", "true");
        }
        else{
            $("input[name='representative_firstname']").parent().parent().parent().addClass('d-none')
            $("input[name='representative_lastname']").parent().parent().parent().addClass('d-none')
            $("input[name='representative_firstname']").removeAttr('required');
            $("input[name='representative_lastname']").removeAttr('required');
            $("input[name='representative_firstname']").val('')
            $("input[name='representative_lastname']").val('')
        }
    })
    $("#partner_relationship_selection").change()
});

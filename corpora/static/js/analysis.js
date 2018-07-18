$(document).ready( function() {
    console.log("ready")
})

$(document).on( "submit", 'form#analysis-form', function() {
    // disable to avoid double submission
    $('#analysis-form').find("button").attr('disabled', true);
});

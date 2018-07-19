$(document).on( "submit", 'form#analysis-form', function() {
    // disable to avoid double submission
    $('#analysis-form').find("button").attr('disabled', true);
});

// Submit post on submit
$(document).on( "submit", 'form#save-graph-form', function(event){
  ///console.log($(this).serialize())
  event.preventDefault();
  save_graph($(this));
});

function save_graph(form) {
  $.ajax({
        type: "POST",
        data: form.serialize(),
        url: "graph",

        success: function(json)
        {
            alert(json["message"])
        }
    });
};

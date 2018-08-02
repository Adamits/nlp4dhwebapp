$(document).on( "click", '#btn-download-counts', function(){
  f = $(this).parent("form")

  $.ajax({
        type: "POST",
        data: f.serialize(),
        url: "/corpora/analysis/download",

        success: function(json)
        {
          counts=json["counts"]
          download_counts(counts, 'counts.txt', 'text/plain');
        },
        error: function (xhr, ajaxOptions, thrownError) {
          alert(thrownError);
        }
    });
});

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

function download_counts(counts_string, fn, contentType) {
  var a = document.createElement("a");
  var file = new Blob([counts_string], {type: contentType});
  a.href = URL.createObjectURL(file);
  a.download = fn;
  a.click();
}

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

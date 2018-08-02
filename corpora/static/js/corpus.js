$(document).on( 'click', '.corpora-submit-btn', function() {
    // disable to avoid double submission
    $('.corpora').find('.corpora-submit-btn').attr('disabled', true);
});

$(document).on( 'click', '#corpus-annotate-btn', function() {
    $('.corpora').find('form#corpora-form').attr('action', 'corpora/annotate');
    $('.corpora').find('form#corpora-form').submit();
});

$(document).on( 'click', '#corpus-delete-btn', function() {
    $('.corpora').find('form#corpora-form').attr('action', 'corpora/delete');
    $('.corpora').find('form#corpora-form').submit();
});

$(document).on( 'click', '#corpora-select-all', function() {
    console.log($('.corpora').find('.corpus-checkbox'));
    $('.corpora').find('.corpus-checkbox').prop('checked',true);
});

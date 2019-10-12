$(function() {
      $('#btnsubmit').bind('click', function() {
    // Stop form from submitting normally
    event.preventDefault();
    $('#btnsubmit').attr('disabled', true)
    $('#btnsubmit').text('please wait....')
    $("#submitted").submit();
        });
  });
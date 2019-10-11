$(function() {
    $('#empty').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  $('#empty').attr('disabled', true)
  $('#empty').text('please wait...')
  $("#confirm").submit();
      });
});
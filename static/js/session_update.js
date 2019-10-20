$(function() {
    $('#session_update_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
    $('#session_update_button').attr('disabled', true);
    $('#session_update_button').text("please wait");
    $('#session_update_form').submit()    
    });
  });
  
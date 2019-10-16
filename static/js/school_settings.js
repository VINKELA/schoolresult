
$(function() {
  $('#customize_submit').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
$('#customize_form').submit()
$('#customize_submit').attr('disabled', true)
$('#customize_submit').text('please wait')
   
  });
});
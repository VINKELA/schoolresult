$(function() {
    $('#email_submit').bind('click', function() {
        // Stop form from submitting normally
  event.preventDefault();

     if($('#email_name').val() ==""){
        $('#email_mess').text("please provide your account's email address");
        $('#email_name').focus();
      }
      else{
      $.post( $SCRIPT_ROOT + '/email_ajax',{
        email: $('input[name="email"]').val(),
      }, function(data) {
          if (data == "fail"){
            $('#email_mess').text("no account is account is associated with this email")
            $('#email_name').focus();
          }
          else{
            $("#email_check").submit();
          }
      });}
      
    });
});

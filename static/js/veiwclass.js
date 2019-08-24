$(function() {
    $('#verify_teacher').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#password').val() == ""){
    alert("provide password");
  }

 else{
      $.post( $SCRIPT_ROOT + '/editclass_check',{
        class_id: $('#id').val(),
        password: $('#password').val()
      }, function(data) {
          if (data == "false"){alert("invalid password")}
          else{
            $("#verify_teacher_form").submit();
          }
      });}
    });
  });


  $(function() {
    $('#edit_student_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#firstname').val() == ""){
    alert("provide firstname");
  }
  else if($('#surname').val() == ""){
    alert("provide surname");
  }

 else{
    $("#edit_student_form").submit();
      }
    });
  });


  $(function() {
    $('#add_student_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#password').val() == ""){
    alert("you must provide a password");
  }

 else{
      $.post( $SCRIPT_ROOT + '/editclass_check',{
        class_id: $('#class_id').val(),
        password: $('#password').val()
      }, function(data) {
          if (data == "false"){alert("invalid password")}
          else{
            $("#add_student_form").submit();
          }
      });}
    });
  });

  $(function() {
    $('#add_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#firstname').val() == ""){
    alert("provide firstname");
  }
  else if($('#surname').val() == ""){
    alert("provide surname");
  }

 else{
    $("#add_student_form").submit();
      }
    });
  });

  $(function() {
    $('#password_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('input[name="password"]').val() == ""){
    alert("you must provide a password");
  }

  else{
    $.post( $SCRIPT_ROOT + '/admin_check',{
      password: $('input[name="password"]').val()
    }, function(data) {
        if (data != 'correct'){ 
          alert(data)
        }
        else{
          $("#password_form").submit();};
    });}
  });
});
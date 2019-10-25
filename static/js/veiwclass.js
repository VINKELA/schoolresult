$(function() {
    $('#verify_teacher').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#password').val() == ""){
    $('#teacher_msg').text("provide password");
    $('#password').focus()
  }

 else{
      $.post( $SCRIPT_ROOT + '/editclass_check',{
        class_id: $('#id').val(),
        password: $('#password').val()
      }, function(data) {
          if (data == "false"){
            $('#teacher_msg').text("incorrect password");
            $('#password').focus()
          }
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
    $('#firstname_msg').text('firstname is empty!')
    $('#firstname').focus()
  }
  else if($('#surname').val() == ""){   
     $('#surname_msg').text('surname is empty!')
     $('#surname').focus()
  }
 else{
   $('#edit_student_button').attr('disabled', true)
    $("#edit_student_button").text('please wait');
    $("#edit_student_form").submit();
      }
    });
  });


  $(function() {
    $('#add_student_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('#password').val() == ""){
    $("#msg_pass").text("password is empty");
    $('#add_student_button').focus()
  }

 else{
      $.post( $SCRIPT_ROOT + '/editclass_check',{
        class_id: $('#class_id').val(),
        password: $('#password').val()
      }, function(data) {
          if (data == "false"){
            $("#msg_pass").text("invalid password")
          }
          else{
            $('#add_student_button').attr('disabled',true)
            $('#add_student_button').attr('please wait')
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
    $('#f_msg').text("firstname is empty");
    $('#firstname').focus()
  }
  else if($('#surname').val() == ""){
    $('#s_msg').text("surname is empty");
    $('#surname').focus()
  }

 else{
    $("#add_button").attr("disabled", true)
    $("#add_button").text("please wait")
    $("#add_student_form").submit();
      }
    });
  });

  $(function() {
    $('#password_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('input[name="password"]').val() == ""){
    $('.red').text('')
    $('#admin_msg').text("please enter admin password");
    $('input[name="password"]').focus()
  }

  else{
    $.post( $SCRIPT_ROOT + '/admin_check',{
      password: $('input[name="password"]').val()
    }, function(data) {
        if (data != 'correct'){ 
          $('.red').text('')
          $('#admin_msg').text("incorrect password");
          $('input[name="password"]').focus()
              }
        else{
          $('.red').text('')
          $("#password_form").submit();
        };
    });}
  });
});


$(function() {
  $('#admin_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
if($('input[name="password"]').val() == ""){
  $('#msg_pass').text("password is empty");
  $('input[name="password"]').focus()
}
  else{
    $.post( $SCRIPT_ROOT + '/admin_check',{
      password: $('input[name="password"]').val()
    }, function(data) {
        if (data == "incorrect password"){
          $('#msg_pass').text("incorrect  password")
        }
        else{
          $('#admin_button').attr('disabled', true)
          $('#admin_form').submit()
                }
    });}

    
  });
});


$(function() {
  $('#unregister_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
  $('#unregister_button').attr('disabled', true);
  $('#unregister_button').text("please wait");
  $('#unregister_form').submit()    
  });
});

$(function() {
  $('#confirm_student_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
  $('#confirm_student_button').attr('disabled', true);
  $('#confirm_student_button').text("please wait");
  $('#confirm_student_form').submit()    
  });
});

$(function() {
  $('#teacher_customize_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
if($('#password').val() == ""){
  $('#teacher_customize_button').focus();
  $('#teach_msg').text("password is empty");
}

else{
    $.post( $SCRIPT_ROOT + '/editclass_check',{
      class_id: $('#class_id').val(),
      password: $('#password').val()
    }, function(data) {
        if (data == "false"){
          $('#teach_msg').text("incorrect password");
        }
        else{
          $("#teacher_customize_form").submit();
        }
    });}
  });
});

$(function() {
  $('#class_customize_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
  $('#class_customize_button').attr('disabled', true);
  $('#class_customize_button').text("please wait");
  $('#class_customize_form').submit()    
  });
});

$(function() {
  $('#edit_scoresheet_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
if($('#password').val() == ""){
  $('#password').focus()
  $('#teacher_msg').text("provide password");
}

else{
    $.post( $SCRIPT_ROOT + '/editclass_check',{
      class_id: $('#id').val(),
      password: $('#password').val()
    }, function(data) {
        if (data == "false"){
          $('#teacher_msg').text("incorrect password");
        }
        else{
          $("#edit_scoresheet_form").submit();
        }
    });}
  });
});


$(function() {
  $('#edited_scoresheet_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
if($('#subject_name').val() == ""){
  $('#subject_msg').text("subject does not have a name");
  $('#subject_name').focus()
}
else if($('#teachers_name').val() == ""){
  $('#teachers_msg').text("Teachers name is empty")
  $('#teachers_name').focus();
}
else if ($("#previous_name").val() == $("#subject_name").val()){
  $('#edited_scoresheet_button').attr('disabled',true)
  $('#edited_scoresheet_button').text('please wait')
  $("#edited_scoresheet_form").submit();
}

else{
  $.post( $SCRIPT_ROOT + '/subject_name_check',{
    subject_name: $('input[name="subject_name"]').val(),class_id:$('#class_id').val(), previous:$("#previous").val()
  }, function(data) {
      if (data == "false")
      {
        $('#subject_msg').text($('input[name="subject_name"]').val()+" scoresheet already submitted for selected class")
        $('#subject_name').focus()
      }
      else{
        $('#edited_scoresheet_button').attr('disabled',true)
        $('#edited_scoresheet_button').text('please wait')
        $("#edited_scoresheet_form").submit();
                };
  });};
  });
});

$(function() {
  $('#delete_scoresheet_button').bind('click', function() {
// Stop form from submitting normally
event.preventDefault();
  $('#delete_scoresheet_button').attr('disabled', true);
  $('#delete_scoresheet_button').text("please wait");
  $('#delete_scoresheet_form').submit()    
  });
});

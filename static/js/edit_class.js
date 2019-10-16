$(function() {
    $('#edit_class_button').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  if($('input[name="surname"]').val() == ""){
    $("#surname_msg").text("form teachers surname?");
    $('input[name="surname"]').focus()

  }
  else if($('input[name="firstname"]').val() == ""){
    $("#firstname_msg").text("form teachers firstname?");
    $('input[name="firstname"]').focus()
  }
  else if($('input[name="class_name"]').val() == ""){
    $("#class_msg").text("class does not have a name?");
    $('input[name="class_name"]').focus()
  }
  else if($('input[name="password"]').val() == ""){
    $("#pass_msg").text("password is empty");
    $('input[name="password"]').focus()
  }
  else if($('#ca').val() == ""){
    $('#ca').focus()
    $("#ca_msg").text("password is empty");
  }
  else if($('#test').val() == ""){
    $('#test').focus()
    $("#test_msg").text("password is empty");
  }
  else if($('#exam').val() == ""){
    $('#exam').focus()
    $("#exam_msg").text("password is empty");
  }
  else if($('#section').val() == ""){
    $('#section').focus()
    $("#section_msg").text("password is empty");
  }

 else{
   
            $("#edit_class_button").attr("disabled", true);
            $("#edit_class_button").text("please wait");
            $("#edit_class_form").submit();
        
     }
    });
  });

  $(function() {
    $('#delete').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  $("#delete").attr("disabled", true);
  $("#delete").text("please wait");
  $("#delete_form").submit();
    });
  });
$(function() {
    $('#submit_scoresheet').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  $('#submit_scoresheet').attr('disabled', true)
  if($('input[name="subject_name"]').val() == ""){
    $('#subject_message').text("subject name is empty!");
    $('input[name="subject_name"]').focus()
    $('#submit_scoresheet').attr('disabled', false)

  }

  else if($('#your_class').find(":selected").val() ==""){
    $('#class_message').text("Scoresheet is for which class? select");
    $('#your_class').focus()
    $('#submit_scoresheet').attr('disabled', false)

  }

   else if($('input[name="subject_teacher"]').val() ==""){
    $('#teacher_message').text("please provide the subject teachers name");
    $('input[name="subject_teacher"]').focus()
    $('#submit_scoresheet').attr('disabled', false)
  }
  else{
      $.post( $SCRIPT_ROOT + '/subject_check',{
        subject_name: $('input[name="subject_name"]').val(),class_id:$('#your_class').find(":selected").val()
      }, function(data) {
          if (data == "false")
          {
            $('#subject_message').text($('input[name="subject_name"]').val()+" scoresheet already submitted for "+$('#subject_message'))
            $('#submit_scoresheet').attr('disabled', false)
          }
          else{
            $('#submit_scoresheet').text('please wait ....')
            $("#submit_score").submit();
              };
      });};
      });
});
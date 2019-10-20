$('.form').find('input, textarea').on('keyup blur focus', function (e) {

  var $this = $(this),
      label = $this.prev('label');

	  if (e.type === 'keyup') {
			if ($this.val() === '') {
          label.removeClass('active highlight');
        } else {
          label.addClass('active highlight');
        }
    } else if (e.type === 'blur') {
    	if( $this.val() === '' ) {
    		label.removeClass('active highlight');
			} else {
		    label.removeClass('highlight');
			}
    } else if (e.type === 'focus') {

      if( $this.val() === '' ) {
    		label.removeClass('highlight');
			}
      else if( $this.val() !== '' ) {
		    label.addClass('highlight');
			}
    }

});

$('.tab a,.links a').on('click', function (e) {

  e.preventDefault();

  $(this).parent().addClass('active');
  $(this).parent().siblings().removeClass('active');

  target = $(this).attr('href');

  $('.tab-content > div').not(target).hide();

  $(target).fadeIn(600);

});

addEventListener("load", function() {
  setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); }

addEventListener("load", function()
{ setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); }

$(function() {
    $('#login').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  $('#login').attr('disabled',true);
  if($('input[name="username"]').val() == ""){
    $('#signin_message').text("username is empty")
    $('input[name="username"]').focus()
    $('#login').attr('disabled',false)
  }

 else if($('input[name="password"]').val() ==""){
  $('#password_message').text("password is empty")
  $('input[name="password"]').focus()
  $('#login').attr('disabled',false)
}
 else{
      $.post( $SCRIPT_ROOT + '/login_check',{
        username: $('input[name="username"]').val(),
        password: $('input[name="password"]').val()
      }, function(data) {
          if (data == "fail"){
            $('#signin_message').text("username or password is incorrect")
            $('input[name="username"]').focus()
            $('#login').attr('disabled',false)        
        }
          else{
            $('#login').text("loging in ....")
            $("#login_form").submit();

          }
      });}
    });
  });

  $(function() {
    $('#check_result').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();
  $('#check_result').attr('disabled', true)
  if($('input[name="regnumber"]').val() == ""){
    $('#reg_message').text("exam number is empty");
    $('input[name="regnumber"]').focus()
    $('#check_result').attr('disabled', false)

  }
  else{
    var str = $('input[name="regnumber"]').val();
  if(str.length < 6){
    $('#reg_message').text("exam number invalid");
    $('input[name="regnumber"]').focus()
    $('#check_result').attr('disabled', false)
  }

  else if($('input[name="pin"]').val() ==""){
    $('#pin_message').text("pin is empty");
    $('input[name="pin"]').focus()
    $('#check_result').attr('disabled', false)

  }
  else{
      $.post( $SCRIPT_ROOT + '/result_check',{
        regnumber: $('input[name="regnumber"]').val(),
        pin: $('input[name="pin"]').val()
      }, function(data) {
          if (data == "fail"){
            $('#reg_message').text("exam number invalid");
            $('input[name="regnumber"]').focus() 
            $('#check_result').attr('disabled', false)
       
          }
          else if (data == "pin_invalid"){
            $('#pin_message').text("pin is invalid");
            $('input[name="pin"]').focus()
            $('#check_result').attr('disabled', false)
          }
          else{
            $('#check_result').text('checking ....')
            $("#check_results").submit();
            $('#check_result').attr('disabled', false)
            $('#check_result').text('check result')
          }
      });}
    }
    });
  });
  
var myInput2 = document.getElementById("psw");
var length2 = document.getElementById("length2");
// When the user clicks on the password field, show the message box
myInput2.onfocus = function() {
  document.getElementById("message2").style.display = "block";
};

// When the user clicks outside of the password field, hide the message box
myInput2.onblur = function() {
  document.getElementById("message2").style.display = "none";
};


// When the user starts to type something inside the password field
myInput2.onkeyup = function() {

  // Validate length
  if(myInput2.value.length >= 8) {
    length2.classList.remove("invalid");
    length2.classList.add("valid");
  } else {
    length2.classList.remove("valid");
    length2.classList.add("invalid");
  }
};






$(function() {
    $('#but').bind('click', function() {
  // Stop form from submitting normally
  event.preventDefault();

 if($('input[name="password"]').val() ==""){
    $("#pass_msg").text("password is empty");
  }
   else if($('input[name="confirmation"]').val() ==""){
    $("#conf_msg").text("password confirmation is empty");
  }
   else if($('input[name="password"]').val() != $('input[name="confirmation"]').val()){
    $("#conf_msg").text("password and confirmation do not match");
  }
// Validate length
  else if($('input[name="password"]').val().length() < 8) {
    $("#pass_msg").text(" password must be up to 8 digits");
  }
  else{
    $('#but').attr('disabled',true)
    $("#change_form").submit();
  }
});
});



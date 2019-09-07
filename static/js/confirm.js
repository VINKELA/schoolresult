$(document).ready(function () {
     $("#btnSubmit").on('click', function (event) {  
           event.preventDefault();
           alert("hi")
           var el = $(this);
           el.prop('disabled', true);
           setTimeout(function(){el.prop('disabled', false); }, 3000);
     });
});

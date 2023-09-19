$(document).ready(function(){
     $(window).scroll(function(){
var scroll = $(window).scrollTop();
if (scroll >= 57) {
$('#scroll_hide').hide('slow')
}
else{
$('#scroll_hide').show('slow');
}
});
})
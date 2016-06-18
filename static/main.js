'use strict';

//Copyright year
document.getElementById('year').innerHTML = new Date().getFullYear()

$('.modal-trigger').click(function() {
    $('#blanket').fadeIn();
    $(this).siblings('.modal').fadeIn();
});

$('#blanket').click(function() {
    $('#blanket').fadeOut();
    $('.modal').fadeOut();
});

$('#show_email').change(function() {
    $(this).parent('form').submit();
});

$('.flashes').slideDown().delay(2000).slideUp();

'use strict';

//Copyright year
document.getElementById('year').innerHTML = new Date().getFullYear()

//Modal
$('.modal-trigger').click(function() {
    $('#blanket').fadeIn();
    $(this).siblings('.modal').fadeIn();
});
$('#blanket').click(function() {
    $('#blanket').fadeOut();
    $('.modal').fadeOut();
});


//Flashes
$('.flashes').slideDown().delay(2000).slideUp();


//Forms
$('#login-form form').validate({
    rules: {
        username: 'required',
        password: 'required'
    },
    messages: {
        username: 'Please enter your username',
        password: 'Please enter your password'
    }
});
$('#signup-form form').validate({
    rules: {
        username: 'required',
        email: {
            required: true,
            email: true
        },
        password: {
            required: true,
            minLength: 6
        },
        password2: {
            required: true,
            equalTo: '#password',
        }
    },
    messages: {
        username: 'Please enter your username',
        email: {
            required: 'Please enter your email address',
            email: 'Please enter a valid email address'
        },
        password: {
            required: 'Please enter your password',
            minLength: 'Password must be at least 6 characters'
        },
        password2: {
            required: 'Please confirm your password',
            equalTo: 'Passwords must match'
        }
    }
});
$('#signup-form form').submit(function(e) {
    if ($('#myform').valid()) {
        $(this).submit();
    } else {
        e.preventDefault();
    }
});
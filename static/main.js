'use strict';

//Copyright year
document.getElementById('year').innerHTML = new Date().getFullYear();

// Nav user options
$('body').click(function(e) {
    if ($(e.target).parents('#user-options').length) {
        $('#user-options-inner').toggleClass('user-options-inner-showing');
        $('#user-options').css('border', 'none');
    } else {
        $('#user-options-inner').removeClass('user-options-inner-showing');
    }
    if ($(e.target).parents('.notifications').length) {
        $('.notifications-inner').toggleClass('notifications-inner-showing');
    } else {
        $('.notifications-inner').removeClass('notifications-inner-showing');
    }
});

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
$('.flashes').slideDown().delay(1000).slideUp();


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
$.validator.addMethod('regex', function(value, element, regexpr) {          
    return regexpr.test(value);
}, 'Please enter a valid email.');

$('#signup-form form').validate({
    rules: {
        username: {
            required: true,
            regex: /^[a-zA-Z0-9_]+$/
        },
        email: {
            required: true,
            regex: /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i
        },
        password: {
            required: true,
            minlength: 6
        },
        password2: {
            required: true,
            equalTo: '#password',
        }
    },
    messages: {
        username: {
            required: 'Please enter your username',
            regex: 'Username can only contain letters, numbers, and underscores'
        },
        email: {
            required: 'Please enter your email address',
            regex: 'Please enter a valid email address'
        },
        password: {
            required: 'Please enter your password',
            minlength: 'Password must be at least 6 characters'
        },
        password2: {
            required: 'Please confirm your password',
            equalTo: 'Passwords must match'
        }
    }
});
var valid = false;
$('#signup-form form').submit(function(e) {
    if (valid) {
        
    } else {
        if ($('#signup-form form').valid()) {
            valid = true;
            $(this).submit();
        } else {
            e.preventDefault();
        }
    }
});

// Nav
$('.toggle-nav').click(function() {
    $('nav').slideToggle();
});
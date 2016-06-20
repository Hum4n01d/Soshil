'use strict';

//Copyright year
document.getElementById('year').innerHTML = new Date().getFullYear();

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
$.validator.addMethod('regex', function(value, element, regexpr) {          
    return regexpr.test(value);
}, 'Please enter a valid email.');

$('#signup-form form').validate({
    rules: {
        username: 'required',
        email: {
            required: true,
            regex: /^[\w.]+@[\w.]+.[\w]$/
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
        username: 'Please enter your username',
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
'use strict';

//Copyright year
document.getElementById('year').innerHTML = new Date().getFullYear();

var logged_in = $('.user-options').length;

//Flashes
$('.flashes').slideDown();

$('.flashes').mouseenter(function() {
    $(this).slideUp();
});

setTimeout(function() {
    $('.flashes').slideUp();
}, 3000);

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
            regex: /^[a-zA-Z0-9_​]+$/,
            maxlength: 15
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
$('form').submit(function(e) {
    if (valid) {
        
    } else {
        if ($(this).valid()) {
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


// Delete comment/post confirm
$('button.danger a').click(function(e) {
    e.preventDefault();

    if (confirm('Are you sure? You cannot undo this action.')) {
        window.location = $(this).attr('href')
    }
});

function update_notification() {
    $.ajax({url: '/notifications/get', success: function(data){
        var $el = $('#notification-count');
        var $shakeEl = $el.parent().parents();

        $el.text(data);

        if (data == '0') {
            $el.hide();
            $shakeEl.removeClass('number-showing');
        } else {
            $el.show();
            $shakeEl.addClass('number-showing');
        }
    }, dataType: "text"});
}

if (logged_in) {
    // Nav user options
    $('body').click(function(e) {
        if ($(e.target).parents('.user-options').length) {
            $('.user-options-inner').slideToggle();
        } else {
            $('.user-options-inner').slideUp();
        }
    });

    update_notification();
    setInterval(function(){
        update_notification()
    }, 3000);
}

if ($('#editor').length) {
    var simplemde = new SimpleMDE({
        element: $('#editor')[0]
    });
}

function isOverflowed(element){
    return element.scrollHeight > element.clientHeight || element.scrollWidth > element.clientWidth;
}

if ($('.post').length) {
    var single_post = $('#editor').length;
    if (single_post) {

    } else {
        $('.post').addClass('post-small-height')
        $('.post .post-content').each(function() {
            var $overflow_el = $(this).children('.post-overflow');

            if (isOverflowed($(this)[0])) {
                $overflow_el.show();
            }
        });
    }
}


$('.like-post').click(function() {
    var post_id = $(this).parents('.post').children('.post-id').text();
    var $el = $(this).children('img');
    var $p = $el.siblings('p');

    $.ajax({url: '/posts/'+post_id+'/like', success: function(data){
        var name;
        var new_num = parseInt($p.text());

        if ($el.attr('src') == '/static/heart.svg') {
            // Not liked yet
            name = 'pink_heart.svg';
            new_num++;
        } else {
            name = 'heart.svg';
            new_num--;
        }

        $el.attr('src', '/static/'+name);
        $p.text(new_num);

    }, dataType: "text"});
});
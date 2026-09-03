// This function gets the passwords typed in by the user on the signup page. If the passwords match, the form is submitted as usual. If the passwords dont match, an error message is displayed.
function check_pwd() {
    const pwd1_input = document.getElementById('signup-pwd1-input');
    const pwd2_input = document.getElementById('signup-pwd2-input');

    const error_txt = document.querySelector('.pwd-error-hide');
    const signup_form = document.querySelector('.signup-form');

    const pwd1 = pwd1_input.value;
    const pwd2 = pwd2_input.value;

    signup_form.addEventListener('submit', function (event) {

        if (pwd1 !== pwd2) {
            error_txt.classList.replace('pwd-error-hide', 'pwd-error-show')

            event.preventDefault();
        }

        else {
            signup_form.submit();
            error_txt.classList.replace('pwd-error-show', 'pwd-error-hide')
    }});
};

// This function changes the class of the burger menu, so it can appear or disappear when clicked on
function show_menu() {
    const menu_links = document.getElementById('menu-links-container')
     
    if (menu_links.classList == 'menu-links-hidden') {
        menu_links.classList.replace('menu-links-hidden', 'menu-links-show');
    }

    else {
        menu_links.classList.replace('menu-links-show', 'menu-links-hidden');
    };
}

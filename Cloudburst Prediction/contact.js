document.getElementById('contactForm').addEventListener('submit', function (event) {
    event.preventDefault();
    let name = document.getElementById('name').value;
    let email = document.getElementById('email').value;
    let message = document.getElementById('message').value;

    if (name && email && message) {
        document.getElementById('formMessage').innerHTML = `Thank you, ${name}, for reaching out to us! We will get back to you at ${email} soon.`;
        document.getElementById('contactForm').reset(); // Clear the form
    } else {
        document.getElementById('formMessage').innerHTML = 'Please fill out all fields!';
        document.getElementById('formMessage').style.color = 'red';
    }
});

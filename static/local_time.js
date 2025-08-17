window.addEventListener('DOMContentLoaded', () => {
    const now = new Date();
    const localTime = now.toISOString();
    const timezoneOffset = now.getTimezoneOffset();

    fetch('/receive_time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            local_time: localTime,
            timezone_offset: timezoneOffset
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('status').textContent = 'Redirecting to your homepage...';
        // After receiving, redirect to /home
        window.location.href = '/home';
    })
    .catch(error => {
        document.getElementById('status').textContent = 'Failed to send local time.';
        console.error('Error:', error);
    });
});
function handleAttendance(action, button) {
    // Show loading overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('d-none');

    // Disable button and show spinner
    const btn = button;
    const spinner = btn.querySelector('.spinner-border');
    const buttonText = btn.querySelector('.button-text');

    btn.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.classList.add('d-none');

    // Get location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                // Make the attendance check request
                fetch('/my/attendance/check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': odoo.csrf_token,
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude
                        },
                    }),
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.result && data.result.success) {
                            // Reload the page to show updated status
                            window.location.reload();
                        } else {
                            // Hide loading overlay
                            loadingOverlay.classList.add('d-none');
                            // Show error message
                            const errorMessage = data.result ? data.result.error : 'Failed to process attendance';
                            alert(errorMessage);
                            // Reset button state
                            btn.disabled = false;
                            spinner.classList.add('d-none');
                            buttonText.classList.remove('d-none');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        // Hide loading overlay
                        loadingOverlay.classList.add('d-none');
                        alert('Failed to process attendance. Please try again.');
                        // Reset button state
                        btn.disabled = false;
                        spinner.classList.add('d-none');
                        buttonText.classList.remove('d-none');
                    });
            },
            function (error) {
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                let message = 'Location error: ';
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        message += 'Please enable location access.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message += 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        message += 'Location request timed out.';
                        break;
                    default:
                        message += 'Unknown error occurred.';
                }
                alert(message);
                // Reset button state
                btn.disabled = false;
                spinner.classList.add('d-none');
                buttonText.classList.remove('d-none');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        // Hide loading overlay
        loadingOverlay.classList.add('d-none');
        alert('Geolocation is not supported by your browser');
        // Reset button state
        btn.disabled = false;
        spinner.classList.add('d-none');
        buttonText.classList.remove('d-none');
    }
}

function handleAttendanceWithLocation(action, button) {
    // Show loading overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('d-none');

    // Disable button and show spinner
    const btn = button;
    const spinner = btn.querySelector('.spinner-border');
    const buttonText = btn.querySelector('.button-text');

    btn.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.classList.add('d-none');

    // Get location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                // Make the attendance check request
                fetch('/my/attendance/check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': odoo.csrf_token,
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude
                        },
                    }),
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.result && data.result.success) {
                            // Reload the page to show updated status
                            window.location.reload();
                        } else {
                            // Hide loading overlay
                            loadingOverlay.classList.add('d-none');
                            // Show error message
                            const errorMessage = data.result ? data.result.error : 'Failed to process attendance';
                            alert(errorMessage);
                            // Reset button state
                            btn.disabled = false;
                            spinner.classList.add('d-none');
                            buttonText.classList.remove('d-none');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        // Hide loading overlay
                        loadingOverlay.classList.add('d-none');
                        alert('Failed to process attendance. Please try again.');
                        // Reset button state
                        btn.disabled = false;
                        spinner.classList.add('d-none');
                        buttonText.classList.remove('d-none');
                    });
            },
            function (error) {
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                let message = 'Location error: ';
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        message += 'Please enable location access.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message += 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        message += 'Location request timed out.';
                        break;
                    default:
                        message += 'Unknown error occurred.';
                }
                alert(message);
                // Reset button state
                btn.disabled = false;
                spinner.classList.add('d-none');
                buttonText.classList.remove('d-none');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        // Hide loading overlay
        loadingOverlay.classList.add('d-none');
        alert('Geolocation is not supported by your browser');
        // Reset button state
        btn.disabled = false;
        spinner.classList.add('d-none');
        buttonText.classList.remove('d-none');
    }
} 
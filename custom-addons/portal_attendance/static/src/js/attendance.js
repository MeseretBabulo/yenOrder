function handleAttendanceClick(action) {
    const csrf_token = document.querySelector('input[name="csrf_token"]').value;

    // First, get user attendance data
    fetch('/hr_attendance/attendance_user_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {},
            id: new Date().getTime()
        }),
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            // Then make the check in/out request
            return fetch('/hr_attendance/systray_check_in_out', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrf_token
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {},
                    id: new Date().getTime()
                }),
                credentials: 'same-origin'
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.result) {
                location.reload();
            } else {
                alert(data.error || 'An error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request');
        });
}

// Add function to update attendance status periodically
function updateAttendanceStatus() {
    const csrf_token = document.querySelector('input[name="csrf_token"]').value;

    fetch('/hr_attendance/attendance_user_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {},
            id: new Date().getTime()
        }),
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.result) {
                const status = document.getElementById('attendance-status');
                if (status && data.result.attendance_state === 'checked_in') {
                    // Update duration if checked in
                    const duration = document.getElementById('duration');
                    if (duration) {
                        duration.textContent = 'Duration: ' + data.result.last_attendance_worked_hours.toFixed(2) + ' hours';
                    }
                }
            }
        })
        .catch(error => console.error('Error updating status:', error));
}

// Update status every minute
setInterval(updateAttendanceStatus, 60000);
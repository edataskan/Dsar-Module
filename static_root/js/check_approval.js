document.addEventListener("DOMContentLoaded", () => {
    const checkApprovalUrl = "{% url 'check_approval_and_upload_key_status' %}";

    fetch(checkApprovalUrl, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.need_public_key_upload) {
            window.location.href = "{% url 'upload_public_key' %}";
        }
    })
    .catch(error => console.error('Error:', error));
});

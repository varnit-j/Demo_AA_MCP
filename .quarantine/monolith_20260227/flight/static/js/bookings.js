function popup(element) {
    let ref = element.dataset.ref;
    document.querySelector("#cancel_ticket_btn").dataset.ref = ref;
    document.querySelector(".popup").style.display = 'block';
}

function remove_popup() {
    document.querySelector(".popup").style.display = 'none';
    document.querySelector("#cancel_ticket_btn").dataset.ref = "";
}

function cancel_tkt() {
    let ref = document.querySelector("#cancel_ticket_btn").dataset.ref;
    let formData = new FormData();
    formData.append('ref',ref)
    fetch('ticket/cancel',{
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(response => {
        if (response.success === true) {
            remove_popup();
            document.querySelector(`[id='${ref}'] .ticket-action-div`).innerHTML = '';
            document.querySelector(`[id='${ref}'] .status-div`).innerHTML = `<div class="red">CANCELLED</div>`;
            document.querySelector(`[id='${ref}'] .booking-date-div`).innerHTML = '';
            
            // Show success message with refund information
            if (response.message) {
                alert(`✅ ${response.message}\n\n💰 Loyalty points have been reversed and restored to your account.`);
            } else {
                alert('✅ Ticket cancelled successfully! Refund and loyalty points reversal processed.');
            }
        }
        else {
            remove_popup();
            alert(`❌ Error: ${response.error}`)
        }
    })
    .catch(error => {
        remove_popup();
        alert('❌ Network error occurred. Please try again.');
        console.error('Cancellation error:', error);
    });
}
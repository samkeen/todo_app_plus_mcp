// JavaScript for Todo UI

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    if (flashMessages.length > 0) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.style.opacity = '0';
                setTimeout(() => message.style.display = 'none', 300);
            });
        }, 5000);
    }

    // Format dates on the client side (this would be used if we didn't use a server-side filter)
    const formatDates = function() {
        const dateElements = document.querySelectorAll('.format-date');
        
        dateElements.forEach(function(element) {
            const date = new Date(element.textContent);
            if (!isNaN(date)) {
                element.textContent = date.toLocaleString();
            }
        });
    };
    
    // formatDates();  // Uncomment if using client-side date formatting
});

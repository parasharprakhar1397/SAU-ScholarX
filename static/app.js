// SAU ScholarX - Client Enhancement Script

document.addEventListener('DOMContentLoaded', () => {
    // 1. File input display enhancement
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                const names = Array.from(files).map(f => f.name).join(', ');
                let feedback = input.parentElement.querySelector('.file-feedback');
                if (!feedback) {
                    feedback = document.createElement('div');
                    feedback.className = 'file-feedback';
                    feedback.style.fontSize = '0.8rem';
                    feedback.style.color = '#2563eb';
                    feedback.style.marginTop = '6px';
                    feedback.style.fontWeight = '600';
                    input.parentElement.appendChild(feedback);
                }
                feedback.textContent = `Selected (${files.length} file${files.length > 1 ? 's' : ''}): ${names}`;
            }
        });
    });

    // 2. Flash message auto-dismiss after 6 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.transition = 'opacity 0.4s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 400);
            }
        }, 6000);
    });

    // 3. Confirm prompts for sensitive status actions
    const decisionForms = document.querySelectorAll('.inline-decision-form');
    decisionForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const select = form.querySelector('select[name="status"]');
            if (select && select.value === 'Rejected') {
                if (!confirm('Are you sure you want to mark this application as Rejected?')) {
                    e.preventDefault();
                }
            }
        });
    });
});

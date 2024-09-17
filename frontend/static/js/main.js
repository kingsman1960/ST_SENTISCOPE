document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const results = document.getElementById('results');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);

        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            results.innerHTML = `
                <h2>Analysis Results</h2>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `;
        })
        .catch(error => {
            console.error('Error:', error);
            results.innerHTML = '<p>An error occurred during analysis.</p>';
        });
    });
});
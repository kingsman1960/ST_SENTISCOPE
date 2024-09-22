document.addEventListener('DOMContentLoaded', function() {
    const sectorForm = document.getElementById('sector-form');
    const articleForm = document.getElementById('article-form');
    const results = document.getElementById('results');
    const sectorSelect = document.getElementById('sector-select');

    // Populating the dropdown
    fetch('/get_sectors')
        .then(response => response.json())
        .then(sectors => {
            sectors.forEach(sector => {
                const option = document.createElement('option');
                option.value = sector;
                option.textContent = sector;
                sectorSelect.appendChild(option);
            });
        });

    sectorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(sectorForm);

        fetch('/analyze_sector', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => displayResults(data))
        .catch(handleError);
    });

    articleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(articleForm);

        fetch('/analyze_article', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => displayResults(data))
        .catch(handleError);
    });

    function displayResults(data) {
        results.innerHTML = '<h2>Analysis Results</h2>';
        if (Array.isArray(data)) {
            // Multiple articles (sector analysis)
            data.forEach((article, index) => {
                results.innerHTML += `
                    <div class="article">
                        <h3>${index + 1}. ${article.title}</h3>
                        <p><strong>Source:</strong> ${article.source}</p>
                        <p>${article.description}</p>
                        <h4>Sentiment Analysis:</h4>
                        <pre>${JSON.stringify(article.analysis.sentiment, null, 2)}</pre>
                        <h4>Named Entities:</h4>
                        <pre>${JSON.stringify(article.analysis.entities, null, 2)}</pre>
                    </div>
                `;
            });
        } else {
            // Single article analysis
            results.innerHTML += `
                <h3>Sentiment Analysis:</h3>
                <pre>${JSON.stringify(data.analysis.sentiment, null, 2)}</pre>
                <h3>Named Entities:</h3>
                <pre>${JSON.stringify(data.analysis.entities, null, 2)}</pre>
            `;
        }
    }

    function handleError(error) {
        console.error('Error:', error);
        results.innerHTML = '<p>An error occurred during analysis.</p>';
    }
});
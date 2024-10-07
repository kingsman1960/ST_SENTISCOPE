document.addEventListener('DOMContentLoaded', function() {
    const sectorForm = document.getElementById('sector-form');
    const articleForm = document.getElementById('article-form');
    const results = document.getElementById('results');
    const sectorSelect = document.getElementById('sector-select');
    const overallScoreDiv = document.getElementById('overall-score');
    const overallSentimentSpan = document.getElementById('overall-sentiment');
 
    // Global variables for pagination
    let articlesPerPage = 5;
    let currentPage = 1;
    let totalPages = 1;
 
    // Populate the sector dropdown
    fetch('/get_sectors')
        .then(response => response.json())
        .then(sectors => {
            sectors.forEach(sector => {
                const option = document.createElement('option');
                option.value = sector;
                option.textContent = sector;
                sectorSelect.appendChild(option);
                // Add onchange event listener to the sector select element
                sectorSelect.addEventListener('change', getSectorInfo);
            });
        })
        .catch(error => {
            console.error('Error fetching sectors:', error);
            results.innerHTML = '<p>Error loading sectors.</p>';
        });
 
    // Handle sector form submission
    sectorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(sectorForm);
        const sector = formData.get('sector');
 
        if (!sector) {
            results.innerHTML = '<p>Please select a sector.</p>';
            overallScoreDiv.style.display = 'none';
            return;
        }
 
        results.innerHTML = '<p>Analyzing sector...</p>';
        overallScoreDiv.style.display = 'none';
 
        // Reset currentPage to 1 on new search
        currentPage = 1;
 
        fetch('/analyze_sector', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => { throw data; });
            }
            return response.json();
        })
        .then(data => displaySectorResults(data))
        .catch(error => handleError(error));
    });
 
    // Handle article form submission
    articleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(articleForm);
        const article = formData.get('article');
 
        if (!article) {
            results.innerHTML = '<p>Please paste an article before analyzing.</p>';
            overallScoreDiv.style.display = 'none';
            return;
        }
 
        results.innerHTML = '<p>Analyzing article...</p>';
        overallScoreDiv.style.display = 'none';
 
        fetch('/analyze_article', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => { throw data; });
            }
            return response.json();
        })
        .then(data => displayArticleResults(data))
        .catch(error => handleError(error));
    });
 
    // Displaying results for sector analysis
    function displaySectorResults(data) {
        if (data.error) {
            results.innerHTML = `<p>Error: ${data.error}</p>`;
            overallScoreDiv.style.display = 'none';
            return;
        }
 
        // Display overall sentiment score
        overallSentimentSpan.textContent = data.overall_sentiment;
        overallScoreDiv.style.display = 'block';
 
        // Pagination setup
        const articles = data.articles;
        const totalArticles = articles.length;
        totalPages = Math.ceil(totalArticles / articlesPerPage);
 
        // Ensure currentPage is within bounds
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;
 
        // Calculate start and end indices
        const startIndex = (currentPage - 1) * articlesPerPage;
        const endIndex = startIndex + articlesPerPage;
        const paginatedArticles = articles.slice(startIndex, endIndex);
 
        let html = `<h2>Financial News and Sentiment Analysis</h2>`;
 
        paginatedArticles.forEach((article, index) => {
            const globalIndex = startIndex + index;
            html += `
                <div class="article">
                    <h3>${globalIndex + 1}. <a href="${article.link}" target="_blank">${article.title}</a></h3>
                    <p><strong>Source:</strong> ${article.source}</p>
                    ${article.urlToImage ? `<img src="${article.urlToImage}" alt="${article.title}" width="300">` : ''}
                    <p>${article.description}</p>
                    <h4>Average Sentiment Analysis:</h4>
                    <pre>${JSON.stringify(article.average_sentiments, null, 2)}</pre>
                    <button class="more-button" data-index="${globalIndex}">Details</button>
                    <div class="more-content" id="more-${globalIndex}">
                        <h4>Detailed Sentiment Analysis:</h4>
                        ${displayDetailedSentiments(article.detailed_sentiments)}
                        <h4>Named Entities:</h4>
                        ${displayEntities(article.entities)}
                    </div>
                </div>
                <hr>
            `;
        });
 
        // Add pagination controls
        html += `
            <div class="pagination">
                <button id="prev-page" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                <span>Page ${currentPage} of ${totalPages}</span>
                <button id="next-page" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
            </div>
        `;
 
        results.innerHTML = html;
        addMoreButtonListeners(totalArticles);
 
        // Add event listeners for pagination buttons
        document.getElementById('prev-page').addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                displaySectorResults(data);
            }
        });
 
        document.getElementById('next-page').addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                displaySectorResults(data);
            }
        });
    }
 
    // Displaying results for article analysis
    function displayArticleResults(data) {
        if (data.error) {
            results.innerHTML = `<p>Error: ${data.error}</p>`;
            overallScoreDiv.style.display = 'none';
            return;
        }
 
        // Displaying overall sentiment score
        overallSentimentSpan.textContent = data.overall_sentiment;
        overallScoreDiv.style.display = 'block';
 
        const analysis = data.analysis;
        let html = `<h2>Analysis of Pasted Article</h2>`;
 
        html += `
            <h3>Average Sentiment Analysis:</h3>
            <pre>${JSON.stringify(analysis.average_sentiments, null, 2)}</pre>
            <button class="more-button" data-index="article">Details</button>
            <div class="more-content" id="more-article">
                <h3>Detailed Sentiment Analysis:</h3>
                ${displayDetailedSentiments(analysis.detailed_sentiments)}
                <h3>Named Entities:</h3>
                ${displayEntities(analysis.entities)}
            </div>
        `;
 
        results.innerHTML = html;
        addMoreButtonListeners(1);
    }
 
    // Displaying detailed sentiments
    function displayDetailedSentiments(detailed_sentiments) {
        let html = '';
        for (const [model, sentiments] of Object.entries(detailed_sentiments)) {
            html += `<h4>${model}:</h4>`;
            html += `<pre>${JSON.stringify(sentiments, null, 2)}</pre>`;
        }
        return html;
    }
 
    // Displaying named entities
    function displayEntities(entities) {
        let html = '';
        for (const [source, entity_list] of Object.entries(entities)) {
            html += `<h5>${source} Entities:</h5>`;
            html += `<pre>${JSON.stringify(entity_list, null, 2)}</pre>`;
        }
        return html;
    }
 
    // Events to "Details" buttons
    function addMoreButtonListeners(totalArticles) {
        // Remove existing event listeners to prevent duplicate bindings
        const newButtons = document.querySelectorAll('.more-button');
        newButtons.forEach(button => {
            button.addEventListener('click', function() {
                const index = button.getAttribute('data-index');
                const moreContent = document.getElementById(`more-${index}`);
                if (moreContent.style.display === 'none' || moreContent.style.display === '') {
                    moreContent.style.display = 'block';
                    button.textContent = 'Less';
                } else {
                    moreContent.style.display = 'none';
                    button.textContent = 'Details';
                }
            });
        });
    }
 
    function getSectorInfo() {
        var sector = document.getElementById('sector-select').value;
        if (sector !== 'Manually Paste Article') {
            fetch('/get_sector_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'sector=' + encodeURIComponent(sector)
            })
            .then(response => response.json())
            .then(response => {
                var infoHtml = '<h3>Sector: ' + sector + '</h3>';
                infoHtml += '<p><strong>Description:</strong> ' + response.description + '</p>';
                infoHtml += '<p><strong>Constituents:</strong> ' + response.tickers.join(', ') + '</p>';
 
                // Create a modal or popup to display the information
                var modal = document.createElement('div');
                modal.innerHTML = infoHtml;
                modal.style.position = 'fixed';
                modal.style.left = '50%';
                modal.style.top = '50%';
                modal.style.transform = 'translate(-50%, -50%)';
                modal.style.backgroundColor = 'white';
                modal.style.padding = '20px';
                modal.style.border = '1px solid black';
                modal.style.zIndex = '1000';
 
                // Add a close button
                var closeButton = document.createElement('button');
                closeButton.innerHTML = 'Close';
                closeButton.onclick = function() {
                    document.body.removeChild(modal);
                };
                modal.appendChild(closeButton);
 
                document.body.appendChild(modal);
            })
            .catch(error => {
                console.log('Error:', error);
            });
        }
    }
 
    // Handle errors during fetch
    function handleError(error) {
        console.error('Error:', error);
        if (error.error) {
            results.innerHTML = `<p>Error: ${error.error}</p>`;
        } else {
            results.innerHTML = '<p>An unexpected error occurred during analysis.</p>';
        }
        overallScoreDiv.style.display = 'none';
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('form');
    const searchInput = document.querySelector('input[name="q"]');
    const searchResults = document.getElementById('search-results');

    if (searchForm && searchInput && searchResults) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const jobs = await response.json();
                    updateSearchResults(jobs);
                } catch (error) {
                    console.error('Error fetching search results:', error);
                }
            }
        });
    }

    function updateSearchResults(jobs) {
        searchResults.innerHTML = '';
        jobs.forEach(job => {
            const jobElement = document.createElement('div');
            jobElement.className = 'bg-white p-6 rounded-lg shadow-md mb-4';
            jobElement.innerHTML = `
                <h2 class="text-xl font-semibold mb-2">${job.title}</h2>
                <h3 class="text-lg text-gray-600 mb-2">${job.company}</h3>
                <p class="text-gray-600 mb-4">${job.description}</p>
                <a href="/company/${job.company_id}" class="text-blue-500 hover:underline">View Company</a>
            `;
            searchResults.appendChild(jobElement);
        });
    }
});

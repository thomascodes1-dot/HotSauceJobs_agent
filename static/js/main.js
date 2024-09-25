document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('form[action="/search"]');
    const searchInput = searchForm ? searchForm.querySelector('input[name="q"]') : null;
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
        if (jobs.length === 0) {
            searchResults.innerHTML = '<p class="text-gray-600">No jobs found. Try a different search term.</p>';
            return;
        }
        jobs.forEach(job => {
            const jobElement = document.createElement('div');
            jobElement.className = 'bg-white p-6 rounded-lg shadow-md mb-4 hover:shadow-lg transition duration-200';
            jobElement.innerHTML = `
                <h2 class="text-xl font-semibold mb-2">${job.title}</h2>
                <h3 class="text-lg text-gray-600 mb-2">${job.company}</h3>
                <p class="text-gray-600 mb-4">${job.description}</p>
                <a href="/company/${job.company_id}" class="inline-block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition duration-200">View Company</a>
            `;
            searchResults.appendChild(jobElement);
        });
    }

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add mobile menu toggle functionality
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
});

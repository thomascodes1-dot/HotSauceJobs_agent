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
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    const jobs = await response.json();
                    updateSearchResults(jobs);
                } catch (error) {
                    console.error('Error fetching search results:', error);
                    showErrorMessage('An error occurred while searching. Please try again.');
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

    function showErrorMessage(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-r mb-4 shadow-sm';
        errorElement.innerHTML = `
            <p class="font-bold">Error</p>
            <p>${message}</p>
        `;
        searchResults.innerHTML = '';
        searchResults.appendChild(errorElement);
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

    // Global error handler
    window.addEventListener('error', function(event) {
        console.error('Uncaught error:', event.error);
        showErrorMessage('An unexpected error occurred. Please try refreshing the page.');
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showErrorMessage('An unexpected error occurred. Please try refreshing the page.');
    });
});

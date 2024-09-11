document.addEventListener('DOMContentLoaded', () => {
    // Existing code...

    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    
    const enableDarkMode = () => {
        body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'enabled');
    };
    
    const disableDarkMode = () => {
        body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', null);
    };
    
    if (darkModeToggle) {
        if (localStorage.getItem('darkMode') === 'enabled') {
            enableDarkMode();
            darkModeToggle.checked = true;
        }
        
        darkModeToggle.addEventListener('change', () => {
            if (darkModeToggle.checked) {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        });
    }

    // Loading spinner for infinite scroll
    const loadingSpinner = document.createElement('div');
    loadingSpinner.className = 'loading-spinner hidden';
    loadingSpinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    document.body.appendChild(loadingSpinner);

    // Modify the loadMoreJobs function
    const loadMoreJobs = async () => {
        loadingSpinner.classList.remove('hidden');
        const response = await fetch(`/api/jobs?page=${page}`);
        const data = await response.json();
        if (data.jobs.length > 0) {
            const jobListingsContainer = document.querySelector('#job-listings');
            data.jobs.forEach(job => {
                const jobElement = createJobElement(job);
                jobListingsContainer.appendChild(jobElement);
            });
            page++;
        }
        loadingSpinner.classList.add('hidden');
    };

    // Existing code...
});

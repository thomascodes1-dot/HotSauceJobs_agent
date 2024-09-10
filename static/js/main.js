document.addEventListener('DOMContentLoaded', () => {
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add animation to job listings
    const jobListings = document.querySelectorAll('.job-listing');
    jobListings.forEach((listing, index) => {
        listing.style.animationDelay = `${index * 0.1}s`;
        listing.classList.add('animate-fade-in');
    });

    // Toggle mobile menu
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Add scroll-to-top button functionality
    const scrollToTopBtn = document.getElementById('scroll-to-top');
    if (scrollToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 100) {
                scrollToTopBtn.classList.remove('hidden');
            } else {
                scrollToTopBtn.classList.add('hidden');
            }
        });

        scrollToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Add form validation to job application form
    const applicationForm = document.getElementById('job-application-form');
    if (applicationForm) {
        applicationForm.addEventListener('submit', (e) => {
            const coverLetter = document.getElementById('cover_letter');
            const resume = document.getElementById('resume');
            let isValid = true;

            if (!coverLetter.value.trim()) {
                isValid = false;
                showError(coverLetter, 'Cover letter is required');
            } else {
                hideError(coverLetter);
            }

            if (!resume.value) {
                isValid = false;
                showError(resume, 'Resume is required');
            } else {
                hideError(resume);
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    function showError(input, message) {
        const errorElement = input.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.textContent = message;
        } else {
            const error = document.createElement('p');
            error.className = 'error-message text-red-500 text-sm mt-1';
            error.textContent = message;
            input.parentNode.insertBefore(error, input.nextSibling);
        }
        input.classList.add('border-red-500');
    }

    function hideError(input) {
        const errorElement = input.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
        input.classList.remove('border-red-500');
    }
});

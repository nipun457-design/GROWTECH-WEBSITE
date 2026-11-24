/**
 * GROWTECH ENGINEERS - Industrial Corporate Script
 * Clean, lightweight client-side interactions for navigation, filtering & validation
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss Flash Alerts after 7 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            } catch (e) {
                alert.style.display = 'none';
            }
        }, 7000);
    });

    // 2. Product Category Filter on /products page
    const filterButtons = document.querySelectorAll('.category-filter-btn');
    const productItems = document.querySelectorAll('.product-grid-item');

    if (filterButtons.length > 0 && productItems.length > 0) {
        filterButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                const targetCategory = this.getAttribute('data-filter');

                // Update active button state
                filterButtons.forEach(btn => btn.classList.remove('active', 'btn-gt-primary'));
                filterButtons.forEach(btn => btn.classList.add('btn-gt-outline'));
                this.classList.remove('btn-gt-outline');
                this.classList.add('active', 'btn-gt-primary');

                // Filter products
                productItems.forEach(function (item) {
                    const itemCategory = item.getAttribute('data-category');
                    if (targetCategory === 'all' || itemCategory === targetCategory) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }

    // 3. Enquiry Form Client-side Validation & Prefill
    const enquiryForms = document.querySelectorAll('.gt-enquiry-form');
    enquiryForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const nameInput = form.querySelector('[name="name"]');
            const emailInput = form.querySelector('[name="email"]');
            const phoneInput = form.querySelector('[name="phone"]');
            const subjectInput = form.querySelector('[name="subject"]');
            const messageInput = form.querySelector('[name="message"]');

            let isValid = true;
            let firstInvalid = null;

            // Name check
            if (nameInput && nameInput.value.trim().length < 2) {
                nameInput.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalid) firstInvalid = nameInput;
            } else if (nameInput) {
                nameInput.classList.remove('is-invalid');
                nameInput.classList.add('is-valid');
            }

            // Email check
            const emailPattern = /^[\w\.-]+@[\w\.-]+\.\w+$/;
            if (emailInput && (!emailInput.value.trim() || !emailPattern.test(emailInput.value.trim()))) {
                emailInput.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalid) firstInvalid = emailInput;
            } else if (emailInput) {
                emailInput.classList.remove('is-invalid');
                emailInput.classList.add('is-valid');
            }

            // Phone check
            const cleanPhone = phoneInput ? phoneInput.value.replace(/[\s\-\(\)\+]/g, '') : '';
            if (phoneInput && (cleanPhone.length < 8 || isNaN(cleanPhone))) {
                phoneInput.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalid) firstInvalid = phoneInput;
            } else if (phoneInput) {
                phoneInput.classList.remove('is-invalid');
                phoneInput.classList.add('is-valid');
            }

            // Subject check
            if (subjectInput && subjectInput.value.trim().length < 3) {
                subjectInput.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalid) firstInvalid = subjectInput;
            } else if (subjectInput) {
                subjectInput.classList.remove('is-invalid');
                subjectInput.classList.add('is-valid');
            }

            // Message check
            if (messageInput && messageInput.value.trim().length < 10) {
                messageInput.classList.add('is-invalid');
                isValid = false;
                if (!firstInvalid) firstInvalid = messageInput;
            } else if (messageInput) {
                messageInput.classList.remove('is-invalid');
                messageInput.classList.add('is-valid');
            }

            if (!isValid) {
                e.preventDefault();
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });
    });

    // 4. Handle query parameters for pre-filling subject and service category
    const urlParams = new URLSearchParams(window.location.search);
    const serviceParam = urlParams.get('service');
    const subjectParam = urlParams.get('subject');

    if (subjectParam) {
        const subjectInput = document.getElementById('subject');
        if (subjectInput && !subjectInput.value) {
            subjectInput.value = subjectParam;
        }
    }

    if (serviceParam) {
        const serviceSelect = document.getElementById('service_category');
        if (serviceSelect) {
            for (let i = 0; i < serviceSelect.options.length; i++) {
                if (serviceSelect.options[i].value.toLowerCase().includes(serviceParam.toLowerCase())) {
                    serviceSelect.selectedIndex = i;
                    break;
                }
            }
        }
        const messageBox = document.getElementById('message');
        if (messageBox && !messageBox.value) {
            messageBox.value = `I am interested in receiving technical specifications and a quotation for ${serviceParam}. Please review our requirement.`;
        }
    }
});

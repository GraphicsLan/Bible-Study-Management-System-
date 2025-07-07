document.addEventListener('DOMContentLoaded', function () {
    // Section references
    const personalDetailsSection = document.getElementById('personalDetails');
    const residencyTypeSection = document.getElementById('residencyTypeSection');
    const campusResidencySection = document.getElementById('campusResidencySection');
    const offCampusResidencySection = document.getElementById('offCampusResidencySection');

    // Button references
    const nextBtn = document.getElementById('nextBtn');
    const residencyTypeBackBtn = document.getElementById('residencyTypeBackBtn');
    const residencyTypeNextBtn = document.getElementById('residencyTypeNextBtn');
    const campusResidencyBackBtn = document.getElementById('campusResidencyBackBtn');
    const offCampusResidencyBackBtn = document.getElementById('offCampusResidencyBackBtn');

    // Residency type radios
    const residencyTypeRadios = document.querySelectorAll('input[name="residencyType"]');

    // Area/estate selects
    const areaSelect = document.getElementById('area');
    const estateSelect = document.getElementById('estate');
    const consentCheckbox = document.getElementById('consentCheckbox');

    // Modal
    const successModal = document.getElementById('successModal');
    const generatedUserId = document.getElementById('generatedUserId');
    const loginRedirect = document.getElementById('loginRedirect');

    // Progress tracker steps
    const steps = document.querySelectorAll('.progress-tracker .step');

    // Estate options
    const estateOptions = {
        "Gate A": ["Booster", "420", "Jacaranda", "Shabab","Rubies"],
        "Gate B": ["wright","car wash", "Ngondu", "Bible Way","Salvation Army"],
        "Njokerio A": ["Brothers", "Booster","Legacy 1", "Makazi", "Runda"],
        "Njokerio B": ["Shiloh Church","Grace Hill","Casten",],
        "Ahero": ["Ahero"]
    };

    // Step navigation helpers
    function showSection(section) {
        [personalDetailsSection, residencyTypeSection, campusResidencySection, offCampusResidencySection].forEach(s => s.classList.remove('active'));
        section.classList.add('active');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        updateProgress(section);
    }

    // Progress tracker logic
    function updateProgress(section) {
        steps.forEach(step => step.classList.remove('active'));
        if (section === personalDetailsSection) {
            steps[0].classList.add('active');
        } else if (section === residencyTypeSection) {
            steps[1].classList.add('active');
        } else if (section === campusResidencySection || section === offCampusResidencySection) {
            steps[2].classList.add('active');
        }
    }

    // Enable next only if residency type selected
    residencyTypeRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            residencyTypeNextBtn.disabled = false;
        });
    });

    // Next from personal details
    nextBtn.addEventListener('click', function () {
        if (!validatePersonalDetails()) {
            alert('Please fill in all required fields correctly.');
            return;
        }
        showSection(residencyTypeSection);
    });

    // Back from residency type
    residencyTypeBackBtn.addEventListener('click', function () {
        showSection(personalDetailsSection);
    });

    // Next from residency type
    residencyTypeNextBtn.addEventListener('click', function () {
        const selected = document.querySelector('input[name="residencyType"]:checked');
        if (!selected) {
            alert('Please select your residency type.');
            return;
        }
        if (selected.value === 'campus') {
            showSection(campusResidencySection);
        } else {
            showSection(offCampusResidencySection);
        }
    });

    // Back from campus halls
    campusResidencyBackBtn.addEventListener('click', function () {
        showSection(residencyTypeSection);
    });

    // Back from off-campus estates
    offCampusResidencyBackBtn.addEventListener('click', function () {
        showSection(residencyTypeSection);
    });

    // Area/estate dynamic select
    areaSelect.addEventListener('change', function () {
        const estates = estateOptions[areaSelect.value] || [];
        estateSelect.innerHTML = estates.length
            ? estates.map(e => `<option value="${e}">${e}</option>`).join('')
            : '<option value="">Select area first</option>';
        estateSelect.disabled = !estates.length;
    });

    // Form validation functions
    function validatePersonalDetails() {
        let valid = true;
        const fullName = document.getElementById('fullName');
        if (!fullName.value.trim()) {
            fullName.classList.add('error');
            valid = false;
        } else {
            fullName.classList.remove('error');
        }
        const phone = document.getElementById('phone');
        if (!/^\d{10}$/.test(phone.value.trim())) {
            phone.classList.add('error');
            valid = false;
        } else {
            phone.classList.remove('error');
        }
        const email = document.getElementById('email');
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
            email.classList.add('error');
            valid = false;
        } else {
            email.classList.remove('error');
        }
        if (!document.querySelector('input[name="gender"]:checked')) valid = false;
        const yearOfStudy = document.getElementById('yearOfStudy');
        if (!yearOfStudy.value) {
            yearOfStudy.classList.add('error');
            valid = false;
        } else {
            yearOfStudy.classList.remove('error');
        }
        const sessionsAttended = document.getElementById('sessionsAttended');
        if (!sessionsAttended.value || sessionsAttended.value < 0) {
            sessionsAttended.classList.add('error');
            valid = false;
        } else {
            sessionsAttended.classList.remove('error');
        }
        if (!document.querySelector('input[name="leaderBefore"]:checked')) valid = false;
        if (!document.querySelector('input[name="leaderNow"]:checked')) valid = false;
        return valid;
    }

    function validateCampusResidency() {
        const hall = document.getElementById('hall');
        if (!hall.value) {
            hall.classList.add('error');
            return false;
        }
        hall.classList.remove('error');
        return true;
    }

    function validateOffCampusResidency() {
        let valid = true;
        if (!areaSelect.value) {
            areaSelect.classList.add('error');
            valid = false;
        } else {
            areaSelect.classList.remove('error');
        }
        if (!estateSelect.value) {
            estateSelect.classList.add('error');
            valid = false;
        } else {
            estateSelect.classList.remove('error');
        }
        if (!consentCheckbox.checked) {
            consentCheckbox.classList.add('error');
            valid = false;
        } else {
            consentCheckbox.classList.remove('error');
        }
        return valid;
    }

    // Form submit 
    document.getElementById('registrationForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const activeSection = document.querySelector('.form-step.active');
        let valid = true;

        // Validate campus residency section
        if (activeSection === campusResidencySection) {
            valid = validateCampusResidency();
            if (!valid) {
                alert('Please select your hall and agree to the consent.');
                return;
            }
        }
        // Validate off-campus residency section
        else if (activeSection === offCampusResidencySection) {
            valid = validateOffCampusResidency();
            if (!valid) {
                alert('Please complete all residency details and agree to the consent.');
                return;
            }
        } else {
            return;
        }

        // Submit form 
        const formData = new FormData(this);

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Show success modal with animation
                generatedUserId.textContent = data.user_id;
                successModal.style.display = 'flex';
                successModal.style.animation = 'modalFadeIn 0.5s ease';

                // Redirect after 5 seconds
                setTimeout(() => {
                    window.location.href = data.loginUrl;
                }, 5000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during registration. Please try again.');
        });
    });

});
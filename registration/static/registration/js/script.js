document.addEventListener('DOMContentLoaded', function () {
    // Section references
    const personalDetailsSection = document.getElementById('personalDetails');
    const residencyInfoSection = document.getElementById('residencyInfoSection');
    
    // Residency option fields
    const campusResidencyFields = document.getElementById('campusResidencyFields');
    const offCampusResidencyFields = document.getElementById('offCampusResidencyFields');
    
    // Button references
    const nextBtn = document.getElementById('nextBtn');
    const residencyBackBtn = document.getElementById('residencyBackBtn');
    
    // Form elements
    const registrationForm = document.getElementById('registrationForm');
    const areaSelect = document.getElementById('area');
    const estateSelect = document.getElementById('estate');
    const residencyTypeRadios = document.querySelectorAll('input[name="residencyType"]');
    
    // Modal elements
    const successModal = document.getElementById('successModal');
    const generatedMemberId = document.getElementById('generatedMemberId');
    const loginRedirect = document.getElementById('loginRedirect');
    const countdownElement = document.getElementById('countdown');

    // Estate options
    const estateOptions = {
        "Gate A": ["Booster", "420", "Jacaranda", "Shabab","Rubies"],
        "Gate B": ["wright","car wash", "Ngondu", "Bible Way","Salvation Army"],
        "Njokerio A": ["Brothers", "Booster","Legacy 1", "Makazi", "Runda"],
        "Njokerio B": ["Shiloh Church","Grace Hill","Casten"],
        "Ahero": ["Ahero"]
    };

    // Show section helper
    function showSection(section) {
        document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
        section.classList.add('active');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        updateProgress(section);
    }

    // Update progress tracker
    function updateProgress(section) {
        document.querySelectorAll('.progress-tracker .step').forEach(step => {
            step.classList.remove('active');
        });
        
        if (section === personalDetailsSection) {
            document.querySelector('.step[data-step="1"]').classList.add('active');
        } else {
            document.querySelector('.step[data-step="2"]').classList.add('active');
        }
    }

    // Show/hide residency fields based on selection
    function updateResidencyFields() {
        const selectedResidency = document.querySelector('input[name="residencyType"]:checked');
        if (!selectedResidency) {
            campusResidencyFields.style.display = 'none';
            offCampusResidencyFields.style.display = 'none';
            return;
        }
        
        if (selectedResidency.value === 'campus') {
            campusResidencyFields.style.display = 'block';
            offCampusResidencyFields.style.display = 'none';
        } else {
            campusResidencyFields.style.display = 'none';
            offCampusResidencyFields.style.display = 'block';
        }
    }

    // validation functions
    function validatePersonalDetails() {
        const requiredFields = ['fullName', 'phone', 'email', 'yearOfStudy'];
        let isValid = true;
        
        requiredFields.forEach(id => {
            const field = document.getElementById(id);
            if (!field.value.trim()) {
                field.classList.add('error');
                isValid = false;
            } else {
                field.classList.remove('error');
            }
        });

        // Basic email format check
        const email = document.getElementById('email');
        if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
            email.classList.add('error');
            isValid = false;
        }

        // Check at least one gender is selected
        if (!document.querySelector('input[name="gender"]:checked')) {
            isValid = false;
        }

        return isValid;
    }

    function validateResidencyInfo() {
        const selectedResidency = document.querySelector('input[name="residencyType"]:checked');
        let isValid = true;
        
        if (!selectedResidency) {
            isValid = false;
            alert('Please select your residency type');
            return isValid;
        }
        
        if (selectedResidency.value === 'campus') {
            const hall = document.getElementById('hall');
            if (!hall.value) {
                hall.classList.add('error');
                isValid = false;
            } else {
                hall.classList.remove('error');
            }
        } else {
            const area = document.getElementById('area');
            const estate = document.getElementById('estate');
            
            if (!area.value) {
                area.classList.add('error');
                isValid = false;
            } else {
                area.classList.remove('error');
            }
            
            if (!estate.value || estate.disabled) {
                estate.classList.add('error');
                isValid = false;
            } else {
                estate.classList.remove('error');
            }
        }
        
        return isValid;
    }

    // Enable estate selection when area is selected
    areaSelect.addEventListener('change', function() {
        estateSelect.innerHTML = estateOptions[this.value] 
            ? estateOptions[this.value].map(e => `<option value="${e}">${e}</option>`).join('')
            : '<option value="">Select area first</option>';
        estateSelect.disabled = !estateOptions[this.value];
    });

    // Update residency fields when residency type changes
    residencyTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateResidencyFields);
    });

    // Event listeners
    nextBtn.addEventListener('click', () => {
        if (validatePersonalDetails()) {
            showSection(residencyInfoSection);
        } else {
            alert('Please fill all required fields correctly.');
        }
    });

    residencyBackBtn.addEventListener('click', () => showSection(personalDetailsSection));

    // Form submission handler
    registrationForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateResidencyInfo()) {
            // Scroll to first error
            const firstError = document.querySelector('.error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        const submitBtn = document.querySelector('.form-step.active button[type="submit"]');
        
        // Set loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const formData = new FormData(registrationForm);
            const response = await fetch(registrationForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Registration failed');
            }
            
            // Only show success modal if registration was successful
            if (data.status === 'success') {
                generatedMemberId.textContent = data.member_id;
                successModal.style.display = 'flex';
                
                // Start countdown for redirect
                let seconds = 5;
                countdownElement.textContent = seconds;
                const countdownInterval = setInterval(() => {
                    seconds--;
                    countdownElement.textContent = seconds;
                    if (seconds <= 0) {
                        clearInterval(countdownInterval);
                        window.location.href = data.loginUrl || "{% url 'login' %}";
                    }
                }, 1000);
            } else {
                throw new Error(data.message || 'Registration failed');
            }

        } catch (error) {
            console.error('Error:', error);
            alert('Registration failed: ' + error.message);
        } 
        finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Complete Registration <i class="fas fa-check"></i>';
        }
    });

    // Manual login redirect
    loginRedirect.addEventListener('click', function() {
        window.location.href = "{% url 'login' %}";
    });

    // Initialize residency fields visibility
    updateResidencyFields();
});
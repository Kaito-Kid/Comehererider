/**
 * Password Validation and Show/Hide Functionality
 * CHR - ComeHere Rider Application
 */

class PasswordValidator {
    constructor() {
        this.forbiddenPasswords = new Set();
        this.loadForbiddenPasswords();
        this.initializePasswordFields();
    }

    // Load forbidden passwords from file
    async loadForbiddenPasswords() {
        try {
            const response = await fetch('/static/forbidden_passwords.txt');
            const text = await response.text();
            const passwords = text.split('\n').map(p => p.trim().toLowerCase()).filter(p => p.length > 0);
            this.forbiddenPasswords = new Set(passwords);
        } catch (error) {
            console.warn('Could not load forbidden passwords list:', error);
        }
    }

    // Initialize all password fields on the page
    initializePasswordFields() {
        document.addEventListener('DOMContentLoaded', () => {
            const passwordInputs = document.querySelectorAll('input[type="password"]');
            passwordInputs.forEach(input => {
                // Skip login password fields that have their own implementation
                if (!input.closest('.login-password-field')) {
                    this.setupPasswordField(input);
                }
            });
        });
    }

    // Setup individual password field with show/hide and validation
    setupPasswordField(passwordInput) {
        const container = passwordInput.parentElement;
        
        // Add show/hide toggle
        this.addShowHideToggle(passwordInput, container);
        
        // Add validation if it's a password creation/update field
        if (this.isPasswordCreationField(passwordInput)) {
            this.addPasswordValidation(passwordInput, container);
        }
    }

    // Check if this is a password creation/update field (not login)
    isPasswordCreationField(input) {
        const fieldNames = ['password', 'new_password'];
        const inputName = input.name || input.id || '';
        
        // Check if it's a creation/update field name
        const isCreationField = fieldNames.some(name => inputName.toLowerCase().includes(name)) && 
                               !inputName.toLowerCase().includes('current') &&
                               !inputName.toLowerCase().includes('confirm');
        
        // Check if it's NOT a login form
        const isNotLoginForm = !this.isLoginForm(input);
        
        return isCreationField && isNotLoginForm;
    }

    // Check if the password field is part of a login form
    isLoginForm(input) {
        // Check if the input is inside a form with login-related ID or class
        const form = input.closest('form');
        if (!form) return false;
        
        const formId = form.id || '';
        const formClass = form.className || '';
        
        // Check for login form identifiers
        return formId.toLowerCase().includes('login') || 
               formClass.toLowerCase().includes('login') ||
               formId === 'loginForm';
    }

    // Add show/hide password toggle
    addShowHideToggle(passwordInput, container) {
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'btn btn-outline-secondary password-toggle';
        toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
        toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
        
        // Style the container for input group
        container.classList.add('input-group');
        
        // Add toggle functionality
        toggleBtn.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            toggleBtn.innerHTML = isPassword ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        });
        
        // Insert toggle button after input
        passwordInput.insertAdjacentElement('afterend', toggleBtn);
    }

    // Add password validation with real-time feedback
    addPasswordValidation(passwordInput, container) {
        // Create validation feedback container
        const validationContainer = document.createElement('div');
        validationContainer.className = 'password-validation mt-2';
        validationContainer.innerHTML = `
            <div class="password-strength-bar mb-2">
                <div class="progress" style="height: 4px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
            </div>
            <div class="password-rules">
                <div class="strong-password-message d-none">
                    <div class="text-success fw-bold">
                        <i class="bi bi-shield-check"></i> Strong Password
                    </div>
                </div>
                <div class="rule-requirements">
                    <small class="text-muted d-block mb-1">Password must contain:</small>
                    <div class="rule-item" data-rule="length">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>At least 8 characters</span>
                    </div>
                    <div class="rule-item" data-rule="uppercase">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>One uppercase letter (A-Z)</span>
                    </div>
                    <div class="rule-item" data-rule="lowercase">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>One lowercase letter (a-z)</span>
                    </div>
                    <div class="rule-item" data-rule="number">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>One number (0-9)</span>
                    </div>
                    <div class="rule-item" data-rule="special">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>One special character (@._)</span>
                    </div>
                    <div class="rule-item" data-rule="forbidden">
                        <i class="bi bi-x-circle text-danger"></i>
                        <span>Not a common password</span>
                    </div>
                </div>
            </div>
        `;
        
        // Insert validation container after the input group
        container.insertAdjacentElement('afterend', validationContainer);
        
        // Add real-time validation
        passwordInput.addEventListener('input', () => {
            this.validatePassword(passwordInput.value, validationContainer);
        });
        
        // Initial validation
        this.validatePassword(passwordInput.value, validationContainer);
    }

    // Validate password against all rules
    validatePassword(password, validationContainer) {
        const rules = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[@._]/.test(password),
            forbidden: !this.forbiddenPasswords.has(password.toLowerCase())
        };

        const allValid = Object.values(rules).every(Boolean);
        const strongMessage = validationContainer.querySelector('.strong-password-message');
        const ruleRequirements = validationContainer.querySelector('.rule-requirements');

        // Show/hide strong password message
        if (allValid && password.length > 0) {
            strongMessage.classList.remove('d-none');
            ruleRequirements.classList.add('d-none');
        } else {
            strongMessage.classList.add('d-none');
            ruleRequirements.classList.remove('d-none');
        }

        // Update rule indicators (only show invalid rules)
        Object.entries(rules).forEach(([rule, isValid]) => {
            const ruleElement = validationContainer.querySelector(`[data-rule="${rule}"]`);
            if (ruleElement) {
                if (isValid) {
                    // Hide valid rules
                    ruleElement.style.display = 'none';
                } else {
                    // Show invalid rules
                    ruleElement.style.display = 'flex';
                    const icon = ruleElement.querySelector('i');
                    icon.className = 'bi bi-x-circle text-danger';
                    ruleElement.classList.add('text-danger');
                    ruleElement.classList.remove('text-success');
                }
            }
        });

        // Update strength bar
        const validRules = Object.values(rules).filter(Boolean).length;
        const strength = (validRules / Object.keys(rules).length) * 100;
        const progressBar = validationContainer.querySelector('.progress-bar');
        
        progressBar.style.width = `${strength}%`;
        progressBar.className = 'progress-bar';
        
        if (strength < 33) {
            progressBar.classList.add('bg-danger');
        } else if (strength < 66) {
            progressBar.classList.add('bg-warning');
        } else if (strength < 100) {
            progressBar.classList.add('bg-info');
        } else {
            progressBar.classList.add('bg-success');
        }

        // Return validation result
        return Object.values(rules).every(Boolean);
    }

    // Public method to validate password (for form submission)
    static validatePasswordRules(password, forbiddenPasswords = new Set()) {
        return {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[@._]/.test(password),
            forbidden: !forbiddenPasswords.has(password.toLowerCase()),
            isValid: function() {
                return this.length && this.uppercase && this.lowercase && 
                       this.number && this.special && this.forbidden;
            }
        };
    }
}

// Initialize password validator
const passwordValidator = new PasswordValidator();

// Export for use in other scripts
window.PasswordValidator = PasswordValidator;

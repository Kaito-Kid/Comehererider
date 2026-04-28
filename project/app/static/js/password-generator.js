/**
 * Password Generator with Random Words + Year
 * CHR - ComeHere Rider Application
 */

class PasswordGenerator {
    constructor() {
        this.words = [
            'Apple', 'Beach', 'Cloud', 'Dream', 'Eagle', 'Forest', 'Garden', 'Happy',
            'Island', 'Journey', 'Knight', 'Light', 'Mountain', 'Nature', 'Ocean', 'Peace',
            'Queen', 'River', 'Star', 'Tiger', 'Unity', 'Victory', 'Wonder', 'Xray',
            'Yellow', 'Zebra', 'Angel', 'Brave', 'Crystal', 'Dragon', 'Energy', 'Fire',
            'Grace', 'Heart', 'Ice', 'Jazz', 'King', 'Love', 'Magic', 'Noble',
            'Opal', 'Power', 'Quest', 'Rose', 'Spirit', 'Thunder', 'Ultra', 'Violet',
            'Wind', 'Xenon', 'Youth', 'Zen', 'Arrow', 'Bloom', 'Charm', 'Dawn',
            'Echo', 'Flame', 'Glow', 'Hope', 'Ivory', 'Jade', 'Karma', 'Luna',
            'Mystic', 'Nova', 'Orbit', 'Pearl', 'Quartz', 'Radiant', 'Sage', 'Titan',
            'Urban', 'Vibe', 'Wave', 'Xylem', 'Yarn', 'Zest', 'Amber', 'Blaze',
            'Coral', 'Dusk', 'Ember', 'Frost', 'Galaxy', 'Harmony', 'Iris', 'Jewel',
            'Kite', 'Lunar', 'Meadow', 'Nectar', 'Oasis', 'Prism', 'Quill', 'Rhythm',
            'Solar', 'Tulip', 'Universe', 'Velvet', 'Willow', 'Xmas', 'Yonder', 'Zephyr'
        ];
        
        this.specialChars = ['@', '.', '_'];
        this.currentYear = new Date().getFullYear();
    }

    // Generate a random password with word + year format
    generatePassword() {
        const randomWord = this.words[Math.floor(Math.random() * this.words.length)];
        const specialChar = this.specialChars[Math.floor(Math.random() * this.specialChars.length)];
        const randomNumber = Math.floor(Math.random() * 99) + 1; // 1-99
        
        // Format: Word.Year or Word@Year or WordSpecialYear
        const formats = [
            `${randomWord}.${this.currentYear}`,
            `${randomWord}@${this.currentYear}`,
            `${randomWord}${specialChar}${this.currentYear}`,
            `${randomWord}${randomNumber}${specialChar}${this.currentYear}`
        ];
        
        return formats[Math.floor(Math.random() * formats.length)];
    }

    // Add generate button to password field
    addGenerateButton(passwordInput, container) {
        // Check if button already exists
        if (container.querySelector('.password-generate')) {
            return;
        }

        // Create generate button
        const generateBtn = document.createElement('button');
        generateBtn.type = 'button';
        generateBtn.className = 'btn btn-outline-info password-generate';
        generateBtn.innerHTML = '<i class="bi bi-magic"></i>';
        generateBtn.setAttribute('aria-label', 'Generate secure password');
        generateBtn.title = 'Generate secure password';
        
        // Add generate functionality
        generateBtn.addEventListener('click', () => {
            const newPassword = this.generatePassword();
            passwordInput.value = newPassword;
            
            // Trigger input event to update validation
            passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Show brief feedback
            this.showGenerateSuccess(generateBtn);
        });
        
        // Insert generate button after toggle button or after input
        const toggleBtn = container.querySelector('.password-toggle');
        if (toggleBtn) {
            toggleBtn.insertAdjacentElement('afterend', generateBtn);
        } else {
            passwordInput.insertAdjacentElement('afterend', generateBtn);
        }
    }

    // Show success feedback for password generation
    showGenerateSuccess(button) {
        const originalContent = button.innerHTML;
        const originalClass = button.className;
        
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.className = 'btn btn-success password-generate';
        
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.className = originalClass;
        }, 1000);
    }

    // Auto-generate password if field is empty on focus out
    setupAutoGenerate(passwordInput) {
        passwordInput.addEventListener('blur', () => {
            if (!passwordInput.value.trim() && this.isPasswordCreationField(passwordInput)) {
                const autoPassword = this.generatePassword();
                passwordInput.value = autoPassword;
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    }

    // Check if this is a password creation field
    isPasswordCreationField(input) {
        const fieldNames = ['password', 'new_password'];
        const inputName = input.name || input.id || '';
        return fieldNames.some(name => inputName.toLowerCase().includes(name)) && 
               !inputName.toLowerCase().includes('current') &&
               !inputName.toLowerCase().includes('confirm');
    }
}

// Initialize password generator
const passwordGenerator = new PasswordGenerator();

// Extend the existing PasswordValidator to include generation
if (window.PasswordValidator) {
    const originalSetupPasswordField = window.PasswordValidator.prototype.setupPasswordField;
    
    window.PasswordValidator.prototype.setupPasswordField = function(passwordInput) {
        // Call original setup
        originalSetupPasswordField.call(this, passwordInput);
        
        // Add generation features for creation fields
        if (passwordGenerator.isPasswordCreationField(passwordInput)) {
            const container = passwordInput.parentElement;
            passwordGenerator.addGenerateButton(passwordInput, container);
            passwordGenerator.setupAutoGenerate(passwordInput);
        }
    };
}

// Export for use in other scripts
window.PasswordGenerator = PasswordGenerator;

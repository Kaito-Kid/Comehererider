/**
 * Credentials Display Component
 * CHR - ComeHere Rider Application
 */

class CredentialsDisplay {
    constructor() {
        this.initializeCredentialsDisplay();
    }

    // Initialize credentials display functionality
    initializeCredentialsDisplay() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupCredentialsToggles();
        });
    }

    // Setup show/hide toggles for credential values
    setupCredentialsToggles() {
        const credentialToggles = document.querySelectorAll('.credential-toggle');
        credentialToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleCredentialVisibility(toggle);
            });
        });
    }

    // Toggle visibility of a credential value
    toggleCredentialVisibility(toggle) {
        const targetId = toggle.getAttribute('data-target');
        const valueElement = document.getElementById(targetId);
        const isHidden = valueElement.classList.contains('credential-hidden');
        
        if (isHidden) {
            // Show the value
            valueElement.classList.remove('credential-hidden');
            valueElement.textContent = valueElement.getAttribute('data-value');
            toggle.innerHTML = '<i class="bi bi-eye-slash"></i>';
            toggle.setAttribute('aria-label', 'Hide value');
        } else {
            // Hide the value
            valueElement.classList.add('credential-hidden');
            valueElement.textContent = '••••••••';
            toggle.innerHTML = '<i class="bi bi-eye"></i>';
            toggle.setAttribute('aria-label', 'Show value');
        }
    }

    // Create credentials display HTML
    static createCredentialsDisplay(credentials) {
        const { username, email, phone, password } = credentials;
        
        return `
            <div class="credentials-display">
                <h5 class="fw-bold mb-3">
                    <i class="bi bi-key-fill text-success"></i>
                    Account Created Successfully
                </h5>
                <p class="text-muted mb-3">
                    Please save these credentials securely. The password will not be shown again.
                </p>
                
                <div class="credential-item">
                    <strong>Username:</strong>
                    <div class="d-flex align-items-center gap-2">
                        <span class="credential-value">${username || 'N/A'}</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary credential-copy" 
                                data-value="${username || ''}" title="Copy username">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                </div>
                
                ${email ? `
                <div class="credential-item">
                    <strong>Email:</strong>
                    <div class="d-flex align-items-center gap-2">
                        <span class="credential-value">${email}</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary credential-copy" 
                                data-value="${email}" title="Copy email">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                </div>
                ` : ''}
                
                ${phone ? `
                <div class="credential-item">
                    <strong>Phone:</strong>
                    <div class="d-flex align-items-center gap-2">
                        <span class="credential-value">${phone}</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary credential-copy" 
                                data-value="${phone}" title="Copy phone">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                </div>
                ` : ''}
                
                <div class="credential-item">
                    <strong>Password:</strong>
                    <div class="d-flex align-items-center gap-2">
                        <span class="credential-value credential-hidden" id="generated-password" 
                              data-value="${password}">••••••••</span>
                        <button type="button" class="btn btn-sm btn-outline-secondary credential-toggle" 
                                data-target="generated-password" aria-label="Show password">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-secondary credential-copy" 
                                data-value="${password}" title="Copy password">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                </div>
                
                <div class="mt-3 p-2 bg-warning bg-opacity-10 border border-warning rounded">
                    <small class="text-warning">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <strong>Important:</strong> Save these credentials immediately. 
                        For security reasons, the password cannot be recovered later.
                    </small>
                </div>
                
                <div class="mt-3 d-flex gap-2">
                    <button type="button" class="btn btn-primary" onclick="window.print()">
                        <i class="bi bi-printer"></i> Print Credentials
                    </button>
                    <button type="button" class="btn btn-outline-primary credential-copy-all" 
                            data-credentials='${JSON.stringify(credentials)}'>
                        <i class="bi bi-clipboard-check"></i> Copy All
                    </button>
                </div>
            </div>
        `;
    }

    // Setup copy functionality for credentials
    static setupCopyButtons(container) {
        // Individual copy buttons
        const copyButtons = container.querySelectorAll('.credential-copy');
        copyButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const value = button.getAttribute('data-value');
                await CredentialsDisplay.copyToClipboard(value);
                CredentialsDisplay.showCopyFeedback(button);
            });
        });

        // Copy all button
        const copyAllButton = container.querySelector('.credential-copy-all');
        if (copyAllButton) {
            copyAllButton.addEventListener('click', async () => {
                const credentials = JSON.parse(copyAllButton.getAttribute('data-credentials'));
                const text = CredentialsDisplay.formatCredentialsText(credentials);
                await CredentialsDisplay.copyToClipboard(text);
                CredentialsDisplay.showCopyFeedback(copyAllButton, 'All copied!');
            });
        }

        // Setup toggle functionality
        const credentialsDisplay = new CredentialsDisplay();
        credentialsDisplay.setupCredentialsToggles();
    }

    // Copy text to clipboard
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
    }

    // Show copy feedback
    static showCopyFeedback(button, message = 'Copied!') {
        const originalContent = button.innerHTML;
        button.innerHTML = `<i class="bi bi-check"></i> ${message}`;
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary', 'btn-outline-primary');
        
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.classList.remove('btn-success');
            button.classList.add(button.classList.contains('credential-copy-all') ? 'btn-outline-primary' : 'btn-outline-secondary');
        }, 2000);
    }

    // Format credentials as text
    static formatCredentialsText(credentials) {
        const { username, email, phone, password } = credentials;
        let text = 'CHR Account Credentials\n';
        text += '========================\n\n';
        
        if (username) text += `Username: ${username}\n`;
        if (email) text += `Email: ${email}\n`;
        if (phone) text += `Phone: ${phone}\n`;
        text += `Password: ${password}\n\n`;
        
        text += 'Please keep these credentials secure.\n';
        text += `Generated on: ${new Date().toLocaleString()}`;
        
        return text;
    }
}

// Initialize credentials display
const credentialsDisplay = new CredentialsDisplay();

// Export for use in other scripts
window.CredentialsDisplay = CredentialsDisplay;

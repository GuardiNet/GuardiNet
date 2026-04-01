function checkPasswordStrength() {
            const password = document.getElementById('new_password').value;
            
            // Check length >= 6
            const lengthOk = password.length >= 6;
            updateRequirement('req-length', lengthOk);
            
            // Check for uppercase
            const uppercaseOk = /[A-Z]/.test(password);
            updateRequirement('req-uppercase', uppercaseOk);
            
            // Check for lowercase
            const lowercaseOk = /[a-z]/.test(password);
            updateRequirement('req-lowercase', lowercaseOk);
            
            // Check for digit
            const digitOk = /[0-9]/.test(password);
            updateRequirement('req-digit', digitOk);
            
            // Check for special character
            const specialOk = /[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]/.test(password);
            updateRequirement('req-special', specialOk);
        }
        
        function updateRequirement(elementId, isMet) {
            const element = document.getElementById(elementId);
            if (isMet) {
                element.classList.remove('unmet');
                element.classList.add('met');
                element.querySelector('.requirement-icon').textContent = '✓';
            } else {
                element.classList.remove('met');
                element.classList.add('unmet');
                element.querySelector('.requirement-icon').textContent = '✗';
            }
        }
        
        // Initial check
        checkPasswordStrength();
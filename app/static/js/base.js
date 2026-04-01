function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const toggleIcon = document.getElementById('toggle-icon');
            
            if (sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
                toggleIcon.innerText = '⬅';
            } else {
                sidebar.classList.add('collapsed');
                toggleIcon.innerText = '➡';
            }
        }

        // Sur mobile, on rétracte par défaut au chargement
        window.addEventListener('DOMContentLoaded', () => {
            if (window.innerWidth <= 768) {
                const sidebar = document.getElementById('sidebar');
                const toggleIcon = document.getElementById('toggle-icon');
                sidebar.classList.add('collapsed');
                toggleIcon.innerText = '➡';
            }
        });
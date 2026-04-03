function editCourse(id, name, prof_id) {
                document.getElementById('edit_course_id').value = id;
                document.getElementById('edit_course_name').value = name;
                document.getElementById('edit_prof_id').value = prof_id;
                document.getElementById('edit-course-modal').style.display = 'block';
            }
            
            function editSchedule(id, course_id, class_id, start_time, end_time, room, event_type) {
                document.getElementById('edit_event_id').value = id;
                document.getElementById('delete_event_id').value = id;
                document.getElementById('edit_sched_course_id').value = course_id;
                document.getElementById('edit_sched_class_id').value = class_id;
                document.getElementById('edit_start_time').value = start_time;
                document.getElementById('edit_end_time').value = end_time;
                document.getElementById('edit_room').value = room || '';
                document.getElementById('edit_event_type').value = event_type || '';
                
                document.getElementById('edit-schedule-modal').style.display = 'block';
            }
            
            function deleteSchedule() {
                if (confirm('Voulez-vous vraiment supprimer cet événement ?')) {
                    document.getElementById('delete-schedule-form').submit();
                }
            }

function changeClass(userId, classId, userName) {
    document.getElementById('change_class_user_id').value = userId;
    if (classId) {
        document.getElementById('change_class_id').value = classId;
    }
    document.getElementById('change-class-user-name').innerText = "Etudiant : " + userName;
    document.getElementById('change-class-modal').style.display = 'block';
}

function openTab(evt, tabName) {
            // Hide all tabs
            const tabs = document.getElementsByClassName('admin-tab-content');
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Remove active class from all buttons
            const buttons = document.getElementsByClassName('admin-tab-btn');
            for (let i = 0; i < buttons.length; i++) {
                buttons[i].classList.remove('active');
            }
            
            // Show selected tab and mark button as active
            document.getElementById(tabName).classList.add('active');
            evt.currentTarget.classList.add('active');
        }

        // Search and filter functionality
        document.getElementById('search')?.addEventListener('input', filterTable);
        document.getElementById('role-filter')?.addEventListener('change', filterTable);

        function filterTable() {
            const searchInput = document.getElementById('search')?.value.toLowerCase() || '';
            const roleFilter = document.getElementById('role-filter')?.value || '';
            const rows = document.querySelectorAll('#users-tbody tr:not(.placeholder-row)');
            
            rows.forEach(row => {
                const searchText = row.dataset.search || '';
                const role = row.dataset.role || '';
                
                const matchSearch = searchText.includes(searchInput);
                const matchRole = !roleFilter || role === roleFilter;
                
                row.style.display = (matchSearch && matchRole) ? '' : 'none';
            });
        }
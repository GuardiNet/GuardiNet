let currentSchedules = [];
    let absentStudentIds = [];

    // Init: set to today and load courses
    document.addEventListener("DOMContentLoaded", () => {
        document.getElementById('dateSelect').valueAsDate = new Date();
        loadSchedules();
    });
    
    function resetGrid() {
        document.getElementById('studentsGrid').innerHTML = '<div class="empty-msg">Séléctionnez un cours puis chargez la liste.</div>';
        document.getElementById('confirmContainer').style.display = 'none';
    }

    async function loadSchedules() {
        const dateStr = document.getElementById('dateSelect').value;
        const scheduleSelect = document.getElementById('scheduleSelect');
        scheduleSelect.innerHTML = '<option value="">Chargement...</option>';
        
        try {
            const res = await fetch(`/api/teacher/schedules_by_date?date=${dateStr}`);
            currentSchedules = await res.json();
            
            scheduleSelect.innerHTML = '<option value="">Sélectionnez un cours pour ce jour...</option>';
            
            if(currentSchedules.length === 0) {
                scheduleSelect.innerHTML = '<option value="">Aucun cours sur votre emploi du temps ce jour.</option>';
                scheduleSelect.disabled = true;
            } else {
                scheduleSelect.disabled = false;
                currentSchedules.forEach((sch, idx) => {
                    const option = document.createElement('option');
                    option.value = idx; 
                    option.textContent = `[${sch.start_time} - ${sch.end_time}] Classe ${sch.class_name} - ${sch.course_name}`;
                    scheduleSelect.appendChild(option);
                });
            }
            resetGrid();
        } catch (e) {
            console.error(e);
            scheduleSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        }
    }

    async function loadStudents() {
        const idxStr = document.getElementById('scheduleSelect').value;
        const dateStr = document.getElementById('dateSelect').value;
        
        if (idxStr === "" || idxStr === undefined) {
            alert('Veuillez d\'abord sélectionner un cours.');
            return;
        }
        
        const schedule = currentSchedules[parseInt(idxStr)];
        const classId = schedule.class_id;
        const courseId = schedule.course_id;
        
        // Load absences to know who is already absent 
        const absRes = await fetch(`/api/teacher/absences?class_id=${classId}&course_id=${courseId}&date=${dateStr}`);
        const currentAbsences = await absRes.json();
        absentStudentIds = currentAbsences.map(a => a.student_id);

        const res = await fetch(`/api/teacher/students/${classId}`);
        const students = await res.json();
        
        const grid = document.getElementById('studentsGrid');
        grid.innerHTML = '';
        
        const container = document.getElementById('confirmContainer');
        if (container) container.style.display = 'block';
        
        if (students.length === 0) {
            grid.innerHTML = '<div class="empty-msg">Aucun étudiant dans cette classe.</div>';
            if (container) container.style.display = 'none';
            return;
        }

        students.forEach(student => {
            const isAbsent = absentStudentIds.includes(student.id);
            const card = document.createElement('div');
            card.className = `student-card ${isAbsent ? 'absent' : ''}`;
            card.onclick = () => toggleAbsenceLocal(student.id, card);
            
            const avatarUrl = (student.profile_pic && student.profile_pic !== 'default.jpg') ? `/static/img/profiles/${student.profile_pic}` : 'https://studio-mir.fr/wp-content/uploads/2022/04/photo-professionelle-cv-job-etudiant-1-1.jpg';
            
            card.innerHTML = `
                <img src="${avatarUrl}" class="student-avatar" alt="Avatar" onerror="this.src='https://studio-mir.fr/wp-content/uploads/2022/04/photo-professionelle-cv-job-etudiant-1-1.jpg'">
                <div class="student-name">${student.firstname} ${student.lastname}</div>
                <div style="font-size: 0.8rem; margin-top: 5px; color: ${isAbsent ? '#c62828' : '#2e7d32'}; font-weight: bold;">
                    ${isAbsent ? 'Absent' : 'Présent'}
                </div>
            `;
            
            grid.appendChild(card);
        });
    }

    function toggleAbsenceLocal(studentId, cardElement) {
        const index = absentStudentIds.indexOf(studentId);
        if (index > -1) {
            absentStudentIds.splice(index, 1);
            cardElement.classList.remove('absent');
            cardElement.querySelector('div:last-child').textContent = 'Présent';
            cardElement.querySelector('div:last-child').style.color = '#2e7d32';
        } else {
            absentStudentIds.push(studentId);
            cardElement.classList.add('absent');
            cardElement.querySelector('div:last-child').textContent = 'Absent';
            cardElement.querySelector('div:last-child').style.color = '#c62828';
        }
    }
    
    async function confirmRollCall() {
        const idxStr = document.getElementById('scheduleSelect').value;
        const dateStr = document.getElementById('dateSelect').value;
        
        if (idxStr === "" || idxStr === undefined) return;
        
        const schedule = currentSchedules[parseInt(idxStr)];
        
        try {
            const res = await fetch('/api/teacher/absences/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    class_id: schedule.class_id,
                    course_id: schedule.course_id, 
                    schedule_id: schedule.schedule_id,
                    date: dateStr,
                    absent_ids: absentStudentIds
                })
            });
            const data = await res.json();
            if (data.success) {
                alert("Appel confirmé et enregistré avec succès !");
            } else {
                alert("Erreur lors de l'enregistrement de l'appel.");
            }
        } catch (e) {
            console.error(e);
            alert("Erreur réseau");
        }
    }
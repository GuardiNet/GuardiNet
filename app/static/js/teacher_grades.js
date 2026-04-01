async function loadStudents() {
        const classId = document.getElementById('classSelect').value;
        const courseId = document.getElementById('courseSelect').value;
        
        if (!classId || !courseId) {
            alert('Veuillez sélectionner une classe et un cours.');
            return;
        }

        const res = await fetch(`/api/teacher/students/${classId}`);
        const students = await res.json();
        
        const gradesRes = await fetch(`/api/teacher/grades?class_id=${classId}&course_id=${courseId}`);
        const grades = await gradesRes.json();
        
        const tbody = document.getElementById('studentsBody');
        tbody.innerHTML = '';
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">Aucun étudiant.</td></tr>';
        } else {
            students.forEach(student => {
                const studentGrades = grades.filter(g => g.student_id === student.id);
                const gradesDisplay = studentGrades.map(g => `${g.value}/20 (${g.exam_name} - coeff ${g.coefficient || 1})`).join('<br>');
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="text-align: left; font-weight: bold;">${student.firstname} ${student.lastname}</td>
                    <td style="font-size: 0.9em; color: #555;">${gradesDisplay || '-'}</td>
                    <td><input type="number" step="0.5" min="0" max="20" class="grade-input" id="grade_${student.id}"></td>
                    <td><button onclick="saveGrade(${student.id})" style="padding: 5px 15px; background: #c1d3c5; border: 1px solid #555; cursor: pointer; border-radius: 4px;">Enregistrer</button></td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        document.getElementById('gradesTable').style.display = 'table';
    }

    async function saveGrade(studentId) {
        const courseId = document.getElementById('courseSelect').value;
        const examName = document.getElementById('examName').value;
        const valInput = document.getElementById(`grade_${studentId}`);
        const value = valInput.value;
        
        if (value === '' || value < 0 || value > 20) {
            alert('Note invalide.');
            return;
        }

        try {
            const res = await fetch('/api/teacher/grades', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' , 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
                body: JSON.stringify({ student_id: studentId, course_id: courseId, value: value, exam_name: examName, coefficient: document.getElementById('examCoeff').value })
            });
            const data = await res.json();
            if (data.success) {
                valInput.value = '';
                valInput.style.backgroundColor = '#d4edda';
                setTimeout(() => valInput.style.backgroundColor = '', 1000);
                // Reload list to show newly added note
                loadStudents();
            } else {
                alert("Erreur lors de l'enregistrement de la note.");
            }
        } catch (e) {
            console.error(e);
            alert("Erreur réseau");
        }
    }
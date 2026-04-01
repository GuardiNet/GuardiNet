document.getElementById('classSelect').addEventListener('change', loadHomeworks);

    async function loadHomeworks() {
        const classId = document.getElementById('classSelect').value;
        const courseId = document.getElementById('courseSelect').value;
        const hwList = document.getElementById('hwList');
        
        if (!classId || !courseId) {
            hwList.innerHTML = '<p style="color: #666; font-style: italic;">Sélectionnez une classe et une matière.</p>';
            return;
        }

        const res = await fetch(`/api/teacher/homeworks?class_id=${classId}&course_id=${courseId}`);
        const homeworks = await res.json();
        
        hwList.innerHTML = '';
        if (homeworks.length === 0) {
            hwList.innerHTML = '<p>Aucun devoir donné pour ce cours.</p>';
        } else {
            homeworks.forEach(hw => {
                const dueText = hw.due_date ? 'Pour le ' + hw.due_date : 'Date non définie';
                hwList.innerHTML += '<div class="hw-card"><div><strong>' + hw.title + '</strong><div style="font-size: 0.8rem; color: #555;">' + (hw.description || '') + '</div></div><div style="font-size: 0.85rem; background: #e0e0e0; padding: 3px 8px; border-radius: 10px;">' + dueText + '</div></div>';
            });
        }
    }

    async function addHomework() {
        const classId = document.getElementById('classSelect').value;
        const courseId = document.getElementById('courseSelect').value;
        const title = document.getElementById('hwTitle').value;
        const desc = document.getElementById('hwDesc').value;
        const dueDate = document.getElementById('hwDueDate').value;

        if (!classId || !courseId || !title) {
            alert('Classe, matière et titre obligatoires.');
            return;
        }

        try {
            const res = await fetch('/api/teacher/homeworks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_id: classId, course_id: courseId, title: title, description: desc, due_date: dueDate })
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('hwTitle').value = '';
                document.getElementById('hwDesc').value = '';
                document.getElementById('hwDueDate').value = '';
                alert('Devoir ajouté avec succès !');
                loadHomeworks();
            } else {
                alert("Erreur lors de l'ajout.");
            }
        } catch (e) {
            console.error(e);
            alert("Erreur réseau");
        }
    }
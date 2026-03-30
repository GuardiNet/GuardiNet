/*
  DATA SHAPE — remplace ce tableau par un fetch() vers ton API Flask :
  fetch('/api/notes') → JSON du même format
*/
const sem1 = [
  {
    name: "Devops", avg: 10,
    details: [
      { label: "Programmation", note: 15.25, coeff: 0.5 },
      { label: "Audit",         note: 16,    coeff: 1 },
      { label: "Site web",      note: 18,    coeff: 1 },
      { label: "Oral",          note: 9,     coeff: 3 },
      { label: "Python",        note: 14.5,  coeff: 1 },
      { label: "Ansible",       note: 2.10,  coeff: 3 },
      { label: "Chiffrement",   note: 20,    coeff: 4 },
    ]
  },
  {
    name: "Cryptographie", avg: 16,
    details: [
      { label: "TP Chiffrement symétrique",  note: 17, coeff: 2 },
      { label: "TP Chiffrement asymétrique", note: 15, coeff: 2 },
      { label: "Examen final",               note: 16, coeff: 3 },
      { label: "Projet PKI",                 note: 16, coeff: 3 },
    ]
  },
  {
    name: "Reverse", avg: 10,
    details: [
      { label: "TP Assembleur",    note: 12, coeff: 2 },
      { label: "Crackme niveau 1", note: 14, coeff: 1 },
      { label: "Crackme niveau 2", note: 6,  coeff: 2 },
      { label: "Examen",           note: 9,  coeff: 3 },
    ]
  },
  {
    name: "Pentest", avg: 8,
    details: [
      { label: "Reconnaissance", note: 12, coeff: 1 },
      { label: "Exploitation",   note: 6,  coeff: 3 },
      { label: "Rapport",        note: 10, coeff: 2 },
      { label: "Présentation",   note: 7,  coeff: 2 },
    ]
  }
];

const sem2 = [
  {
    name: "Sécurité Réseau", avg: 13,
    details: [
      { label: "TP Firewall",  note: 14, coeff: 2 },
      { label: "TP IDS/IPS",   note: 12, coeff: 2 },
      { label: "Examen",       note: 13, coeff: 4 },
      { label: "Projet final", note: 14, coeff: 2 },
    ]
  },
  {
    name: "Cloud & Infrastructure", avg: 11,
    details: [
      { label: "AWS Déploiement", note: 13, coeff: 2 },
      { label: "Kubernetes",      note: 8,  coeff: 3 },
      { label: "Terraform",       note: 11, coeff: 2 },
      { label: "Examen",          note: 12, coeff: 3 },
    ]
  },
  {
    name: "Forensic", avg: 14,
    details: [
      { label: "Analyse mémoire",    note: 16, coeff: 2 },
      { label: "Analyse disque",     note: 13, coeff: 2 },
      { label: "Rapport d'incident", note: 14, coeff: 3 },
      { label: "Examen",             note: 13, coeff: 3 },
    ]
  },
  {
    name: "OSINT & Veille", avg: 15,
    details: [
      { label: "TP Maltego",    note: 15, coeff: 2 },
      { label: "Projet veille", note: 17, coeff: 2 },
      { label: "Rapport OSINT", note: 14, coeff: 3 },
      { label: "Présentation",  note: 15, coeff: 3 },
    ]
  }
];

function noteClass(n) {
  if (n >= 18) return 'perfect';
  if (n >= 12) return 'good';
  if (n >= 8)  return 'warn';
  return 'bad';
}

function buildCard(subject) {
  const card = document.createElement('div');
  card.className = 'subject-card';

  const top = document.createElement('div');
  top.className = 'card-top';
  top.innerHTML = `
    <div class="card-subject">${subject.name}</div>
    <div class="card-avg-row">
      <span class="card-avg-label">Moy :</span>
      <span class="card-avg-value ${noteClass(subject.avg)}">${subject.avg}</span>
    </div>
  `;

  const detail = document.createElement('div');
  detail.className = 'card-detail';
  detail.innerHTML = `
    <table class="detail-table">
      <thead>
        <tr><th>Épreuve</th><th>Note</th><th>Coeff</th></tr>
      </thead>
      <tbody>
        ${subject.details.map(d => `
          <tr>
            <td>${d.label}</td>
            <td><span class="note-val ${noteClass(d.note)}">${d.note}</span></td>
            <td>${d.coeff}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  const arrowWrap = document.createElement('div');
  arrowWrap.className = 'card-arrow-wrap';
  arrowWrap.innerHTML = `
    <button class="toggle-btn" aria-expanded="false">
      <svg width="18" height="11" viewBox="0 0 18 11" fill="none"
           stroke="white" stroke-width="2.5" stroke-linecap="round">
        <path d="M1 1l8 8 8-8"/>
      </svg>
    </button>
  `;

  arrowWrap.querySelector('.toggle-btn').addEventListener('click', () => {
    const btn    = arrowWrap.querySelector('.toggle-btn');
    const isOpen = detail.classList.toggle('open');
    btn.classList.toggle('open', isOpen);
    btn.setAttribute('aria-expanded', String(isOpen));
  });

  card.appendChild(top);
  card.appendChild(detail);
  card.appendChild(arrowWrap);
  return card;
}

function populate(subjects, containerId) {
  const el = document.getElementById(containerId);
  subjects.forEach(s => el.appendChild(buildCard(s)));
}

function setupBanner(bannerId, cardsId) {
  const banner = document.getElementById(bannerId);
  const cards  = document.getElementById(cardsId);
  banner.addEventListener('click', () => {
    const col = banner.classList.toggle('collapsed');
    cards.classList.toggle('hidden', col);
  });
}

populate(sem1, 'cards1');
populate(sem2, 'cards2');
setupBanner('banner1', 'cards1');
setupBanner('banner2', 'cards2');
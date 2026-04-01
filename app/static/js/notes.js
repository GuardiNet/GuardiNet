/*
  DATA SHAPE — remplace ce tableau par un fetch() vers ton API Flask :
  fetch('/api/notes') → JSON du même format
*/


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

if (typeof studentGradesData !== 'undefined') { populate(studentGradesData, 'cards1'); }
setupBanner('banner1', 'cards1');

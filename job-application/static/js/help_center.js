document.addEventListener('DOMContentLoaded', () => {

  if (typeof lucide !== 'undefined') lucide.createIcons();

  const searchInput   = document.getElementById('searchInput');
  const questionsList = document.getElementById('questionsList');
  const questions     = document.querySelectorAll('#questionsList li');
  const catCards      = document.querySelectorAll('.cat-card');
  const noResults     = document.getElementById('noResults');
  const faqCount      = document.getElementById('faqCount');
  const faqResultLabel= document.getElementById('faqResultLabel');

  let activeCategory = 'all';

  questions.forEach(li => {
    const trigger = li.querySelector('.faq-trigger');
    if (!trigger) return;

    trigger.addEventListener('click', () => {
      const isOpen = li.classList.contains('open');

      questions.forEach(other => {
        if (other !== li) {
          other.classList.remove('open');
          const t = other.querySelector('.faq-trigger');
          if (t) t.setAttribute('aria-expanded', 'false');
        }
      });

      li.classList.toggle('open', !isOpen);
      trigger.setAttribute('aria-expanded', String(!isOpen));
    });
  });

  catCards.forEach(card => {
    card.addEventListener('click', () => {
      catCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      activeCategory = card.dataset.category;
      faqResultLabel.textContent = activeCategory === 'all'
        ? 'All articles'
        : activeCategory + ' articles';
      filterQuestions();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', () => filterQuestions());

    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        searchInput.value = '';
        filterQuestions();
      }
    });
  }

  function filterQuestions() {
    const q = searchInput ? searchInput.value.toLowerCase().trim() : '';
    let visible = 0;

    questions.forEach((li, idx) => {
      const questionEl = li.querySelector('.faq-question');
      const bodyEl     = li.querySelector('.faq-body-inner p');
      const tagsAttr   = (li.dataset.tags || '').toLowerCase();
      const category   = li.dataset.category;

      const questionText = questionEl ? questionEl.textContent : '';
      const bodyText     = bodyEl     ? bodyEl.textContent     : '';

      const matchSearch   = !q
        || questionText.toLowerCase().includes(q)
        || bodyText.toLowerCase().includes(q)
        || tagsAttr.includes(q);

      const matchCategory = activeCategory === 'all' || category === activeCategory;

      if (matchSearch && matchCategory) {
        li.style.display = '';
        li.style.animationDelay = (visible * 0.04) + 's';
        visible++;

        if (questionEl) highlightText(questionEl, questionText, q);
        if (bodyEl)     highlightText(bodyEl,     bodyText,     q);
      } else {
        li.style.display = 'none';
        li.classList.remove('open');
      }
    });

    faqCount.textContent = visible;

    if (visible === 0) {
      noResults.style.display = 'block';
      questionsList.style.display = 'none';
    } else {
      noResults.style.display = 'none';
      questionsList.style.display = '';
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
  }

  function highlightText(el, original, term) {
    if (!term) { el.textContent = original; return; }
    const regex = new RegExp(`(${escapeReg(term)})`, 'gi');
    el.innerHTML = original.replace(regex, '<mark>$1</mark>');
  }

  function escapeReg(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  document.querySelectorAll('.demo-dots').forEach(dotsEl => {
    const strip  = dotsEl.closest('.demo-strip');
    const steps  = strip.querySelectorAll('.demo-step');
    const dots   = dotsEl.querySelectorAll('.demo-dot');

    dots.forEach(dot => {
      dot.addEventListener('click', () => {
        const target = dot.dataset.target;
        steps.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));
        const targetStep = strip.querySelector(`.demo-step[data-step="${target}"]`);
        if (targetStep) targetStep.classList.add('active');
        dot.classList.add('active');
        if (typeof lucide !== 'undefined') lucide.createIcons();
      });
    });

    let demoTimer = null;
    const li = strip.closest('li');
    if (li) {
      const observer = new MutationObserver(() => {
        if (li.classList.contains('open')) {
          if (!demoTimer) {
            demoTimer = setInterval(() => advanceDemo(steps, dots, strip), 3000);
          }
        } else {
          clearInterval(demoTimer);
          demoTimer = null;
        }
      });
      observer.observe(li, { attributes: true, attributeFilter: ['class'] });
    }
  });

  function advanceDemo(steps, dots, strip) {
    let current = 0;
    steps.forEach((s, i) => { if (s.classList.contains('active')) current = i; });
    const next = (current + 1) % steps.length;
    steps.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    steps[next].classList.add('active');
    dots[next].classList.add('active');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }

});

function resetSearch() {
  const inp = document.getElementById('searchInput');
  if (inp) { inp.value = ''; inp.dispatchEvent(new Event('input')); }
}

function jumpToArticle(index) {
  const items = document.querySelectorAll('#questionsList li');
  if (!items[index]) return;
  items[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => {
    const trigger = items[index].querySelector('.faq-trigger');
    if (trigger) trigger.click();
  }, 400);
}

function submitFeedback(type, btn) {
  const widget = btn.closest('.feedback-widget');
  const btns   = widget.querySelectorAll('.feedback-btn');
  const thanks = widget.querySelector('.feedback-thanks');

  btns.forEach(b => b.classList.remove('chosen'));
  btn.classList.add('chosen');

  setTimeout(() => {
    btns.forEach(b => { b.style.display = 'none'; });
    thanks.style.display = 'flex';
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }, 600);
}

document.addEventListener("DOMContentLoaded", function() {
  const helpEmailSupportBtn = document.getElementById("helpEmailSupportBtn");

  if (helpEmailSupportBtn) {
    helpEmailSupportBtn.addEventListener("click", function(e) {
      e.preventDefault();
      window.location.href = "/about#our-team";
    });
  }
});

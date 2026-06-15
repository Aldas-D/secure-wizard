// Quiz form validation. Anksčiau buvo inline <script> question.html šablone, bet
// dėl griežtos CSP politikos (jokio 'unsafe-inline') perkeltas į atskirą failą.
(function () {
    'use strict';

    const form = document.getElementById('answerForm');
    if (!form) return;

    const errorMsg = document.getElementById('errorMsg');
    const submitBtn = document.getElementById('submitBtn');

    form.addEventListener('submit', function (e) {
        if (e.submitter && e.submitter.hasAttribute('formnovalidate')) {
            return true;
        }
        const checked = form.querySelectorAll('input[name="answer_id"]:checked');
        if (checked.length === 0) {
            e.preventDefault();
            if (errorMsg) {
                errorMsg.classList.remove('hidden');
                errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            return false;
        }
        if (errorMsg) errorMsg.classList.add('hidden');
        if (submitBtn) submitBtn.disabled = true;
    });

    form.querySelectorAll('input[name="answer_id"]').forEach(function (input) {
        input.addEventListener('change', function () {
            if (errorMsg) errorMsg.classList.add('hidden');
        });
    });
})();

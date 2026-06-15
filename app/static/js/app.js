(function () {
    "use strict";

    document.querySelectorAll("[data-print-page]").forEach(function (button) {
        button.addEventListener("click", function () {
            window.print();
        });
    });

    document.querySelectorAll("[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
})();

document.addEventListener('DOMContentLoaded', function () {
    // Handle nested dropdowns
    document.querySelectorAll('.dropdown').forEach(function (dropdown) {
        dropdown.addEventListener('show.bs.dropdown', function () {
            const submenu = this.querySelector('.dropdown-menu');
            if (submenu) {
                submenu.style.display = 'block';
            }
        });
        dropdown.addEventListener('hide.bs.dropdown', function () {
            const submenu = this.querySelector('.dropdown-menu');
            if (submenu) {
                submenu.style.display = 'none';
            }
        });
    });

    // Re-initialize Bootstrap dropdowns after HTMX swap
    document.body.addEventListener('htmx:afterSwap', function () {
        const dropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdowns.forEach(function (dropdown) {
            new bootstrap.Dropdown(dropdown);
        });
    });
});
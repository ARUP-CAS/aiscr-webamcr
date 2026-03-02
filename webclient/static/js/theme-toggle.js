// Theme Toggle functionality
class ThemeManager {
    constructor() {
        this.THEME_KEY = 'app-theme';
        this.LIGHT_THEME = 'light';
        this.DARK_THEME = 'dark';
        this.init();
    }

    init() {
        // Check system preference or saved preference
        const savedTheme = this.getSavedTheme();
        const prefersDark = this.getSystemPreference();
        const initialTheme = savedTheme || (prefersDark ? this.DARK_THEME : this.LIGHT_THEME);

        this.setTheme(initialTheme);
        this.setupMediaQueryListener();
    }

    getSavedTheme() {
        return localStorage.getItem(this.THEME_KEY);
    }

    getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    setTheme(theme, isManual = false) {
        const html = document.documentElement;
        const isDark = theme === this.DARK_THEME;

        if (isDark) {
            html.setAttribute('data-theme', this.DARK_THEME);
            document.body.classList.add('app-dark-theme');
            document.body.classList.remove('app-light-theme');
        } else {
            html.setAttribute('data-theme', this.LIGHT_THEME);
            document.body.classList.add('app-light-theme');
            document.body.classList.remove('app-dark-theme');
        }

        // Only persist to localStorage if this is a manual user-initiated change
        if (isManual) {
            localStorage.setItem(this.THEME_KEY, theme);
        }
        this.dispatchThemeChangeEvent(theme);
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === this.DARK_THEME ? this.LIGHT_THEME : this.DARK_THEME;
        this.setTheme(newTheme, true);  // true indicates manual user-initiated change
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.LIGHT_THEME;
    }

    setupMediaQueryListener() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!this.getSavedTheme()) {
                const newTheme = e.matches ? this.DARK_THEME : this.LIGHT_THEME;
                this.setTheme(newTheme);
            }
        });
    }

    dispatchThemeChangeEvent(theme) {
        window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }));
    }
}

// Utility function to initialize theme toggle button
function initializeThemeToggleButton(buttonId = 'theme-toggle-btn') {
    if (typeof window.themeManager === 'undefined') {
        // Wait for theme manager to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initializeThemeToggleButton(buttonId);
            });
        } else {
            setTimeout(() => {
                initializeThemeToggleButton(buttonId);
            }, 100);
        }
        return;
    }

    const themeBtn = document.getElementById(buttonId);
    if (!themeBtn) return;

    // Click handler
    themeBtn.addEventListener('click', () => {
        window.themeManager.toggleTheme();
    });

    // Update button icon based on current theme
    window.addEventListener('theme-changed', (e) => {
        const icon = themeBtn.querySelector('.material-icons');
        if (icon) {
            icon.textContent = e.detail.theme === 'dark' ? 'light_mode' : 'dark_mode';
        }
    });

    // Set initial icon
    const initialTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const icon = themeBtn.querySelector('.material-icons');
    if (icon) {
        icon.textContent = initialTheme === 'dark' ? 'light_mode' : 'dark_mode';
    }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
        // Initialize any theme toggle buttons on login/registration pages
        initializeThemeToggleButton();
    });
} else {
    window.themeManager = new ThemeManager();
    initializeThemeToggleButton();
}

/** @type {import('tailwindcss').Config} */
module.exports = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                serif: ['Lora', 'Georgia', 'serif'],
            },
            colors: {
                // ISQ Brand: light background, red accent, dark text
                background: '#f8f8f8',
                foreground: '#1a1a1a',
                card: {
                    DEFAULT: '#ffffff',
                    foreground: '#1a1a1a',
                },
                primary: {
                    DEFAULT: '#d60000',
                    foreground: '#ffffff',
                    light: '#ff1a1a',
                    dark: '#a00000',
                },
                secondary: {
                    DEFAULT: '#f0f0f0',
                    foreground: '#444444',
                },
                muted: {
                    DEFAULT: '#e8e8e8',
                    foreground: '#777777',
                },
                accent: {
                    DEFAULT: '#ff4444',
                    foreground: '#ffffff',
                },
                border: '#e0e0e0',
                input: '#f0f0f0',
                ring: '#d60000',
            },
            borderRadius: {
                lg: '0.75rem',
                md: 'calc(0.75rem - 2px)',
                sm: 'calc(0.75rem - 4px)',
            },
        },
    },
    plugins: [],
};

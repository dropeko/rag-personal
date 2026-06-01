const { join } = require('path');

/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    presets: [require('@data-platforms/ui-lib/tailwind.preset')],
    content: [
        join(__dirname, '{src,pages,components,app}/**/*!(*.stories|*.spec).{ts,tsx,html}'),
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};

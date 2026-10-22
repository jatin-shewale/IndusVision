/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0D1117",
        panel: "#151B23",
        panel2: "#1B232D",
        border: "#262E38",
        amber: "#F0A202",
        safe: "#3DDC84",
        warn: "#F0A202",
        danger: "#FF4D4F",
        textprimary: "#E6EDF3",
        textmuted: "#8B949E",
      },
      fontFamily: {
        display: ["Rajdhani", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

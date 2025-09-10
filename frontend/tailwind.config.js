/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui"] },
      colors: { brand: { DEFAULT: "#f43f5e", dark: "#be123c" } },
      boxShadow: {
        soft: "0 1px 2px rgba(2,6,23,.06), 0 12px 24px -18px rgba(2,6,23,.18)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

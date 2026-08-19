const fs = require('fs');
const path = require('path');

const dir = __dirname;
const html = fs.readFileSync(path.join(dir, 'dashboard-src.html'), 'utf8');
const js = fs.readFileSync(path.join(dir, 'app-src.js'), 'utf8');

function b64(file) {
  return fs.readFileSync(path.join(dir, 'fonts', file), 'utf8').trim();
}

const faces = [
  ['Public Sans', 400, 'public-sans-400.b64.txt'],
  ['Public Sans', 500, 'public-sans-500.b64.txt'],
  ['Public Sans', 600, 'public-sans-600.b64.txt'],
  ['Public Sans', 700, 'public-sans-700.b64.txt'],
  ['JetBrains Mono', 400, 'jetbrains-mono-400.b64.txt'],
  ['JetBrains Mono', 500, 'jetbrains-mono-500.b64.txt'],
  ['JetBrains Mono', 600, 'jetbrains-mono-600.b64.txt'],
];

const fontCss = faces.map(([family, weight, file]) => `@font-face{
  font-family:'${family}';
  font-style:normal;
  font-weight:${weight};
  font-display:swap;
  src:url(data:font/woff2;base64,${b64(file)}) format('woff2');
}`).join('\n');

let out = html.replace('/*__FONT_FACES__*/', () => fontCss);
out = out.replace('/*__APP_JS__*/', () => js);

fs.writeFileSync(path.join(dir, 'dashboard-final.html'), out);
console.log('Wrote dashboard-final.html —', (out.length / 1024 / 1024).toFixed(2), 'MB');

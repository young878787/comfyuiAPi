import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';

const window = new JSDOM('').window;
const purify = DOMPurify(window);

const renderer = {
  code(token) {
    return `<button class="btn-copy" data-code="${encodeURIComponent(token.text)}">Copy</button><pre>${token.text}</pre>`;
  }
};
marked.use({ renderer });
const raw = marked.parse('```\nhello\n```');
console.log("Raw:", raw);

const clean = purify.sanitize(raw);
console.log("Clean:", clean);

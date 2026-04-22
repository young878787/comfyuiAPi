import { marked } from 'marked';
const renderer = {
  code(token) {
    console.log("Token keys:", Object.keys(token));
    console.log("Token type:", token.type);
    console.log("Token text:", token.text);
    return '<pre>' + token.text + '</pre>';
  }
};
marked.use({ renderer });
marked.parse('```\nhello\n```');

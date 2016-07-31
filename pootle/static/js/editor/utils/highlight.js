/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

/* eslint-disable no-irregular-whitespace */
const PUNCTUATION_RE = /[™©®]|[℃℉°]|[±πθ×÷−√∞∆Σ′″]|[‘’ʼ‚‛“”„‟]|[«»]|[£¥€]|…|—|–|[ ]/g;
/* eslint-enable no-irregular-whitespace */
// Marks + Degree-related + Maths + Quote characters + Guillemets + Currencies +
// U2026 horizontal ellipsis + U2014 em dash + U2013 en dash +
// U202F narrow no-break space

export function highlightPunctuation(text, className = '') {
  function replace(match) {
    return `<span class="highlight-punctuation ${className}">${match}</span>`;
  }

  return text.replace(PUNCTUATION_RE, replace);
}


const ESCAPE_RE = /\\r|\\n|\\t/gm;

export function highlightEscapes(text, className = '') {
  const escapeHl = `<span class="highlight-escape ${className}">%s</span>`;
  function replace(match) {
    const submap = {
      '\\r': escapeHl.replace(/%s/, '\\r'),
      '\\n': escapeHl.replace(/%s/, '\\n'),
      '\\t': escapeHl.replace(/%s/, '\\t'),
    };

    return submap[match];
  }

  return text.replace(ESCAPE_RE, replace);
}


const NL_RE = /\r\n|[\r\n]/gm;

export function nl2br(text) {
  return text.replace(NL_RE, '$&<br/>');
}


const HTML_RE = /<[^>]+>|[&<>]/gm;

export function highlightHtml(text, className = '') {
  const htmlHl = `<span class="highlight-html ${className}">&lt;%s&gt;</span>`;
  function replace(match) {
    const submap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
    };

    let replaced = submap[match];

    if (replaced === undefined) {
      replaced = htmlHl.replace(
        /%s/,
        highlightHtml(match.slice(1, match.length - 1))
      );
    }

    return replaced;
  }

  return text.replace(HTML_RE, replace);
}

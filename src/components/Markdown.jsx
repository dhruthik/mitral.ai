// Panellist replies come straight out of the model, and models write markdown
// whether or not you ask them to — **bold**, dashes for lists, back-ticked
// terms. This renders the common subset into React elements rather than HTML:
// the text is untrusted model output, so there is no innerHTML anywhere here
// for it to escape through, and link hrefs are checked before they are used.

const INLINE = /(`+)([\s\S]+?)\1|\*\*([\s\S]+?)\*\*|__([\s\S]+?)__|\*([^*\n]+?)\*|_([^_\n]+?)_|~~([\s\S]+?)~~|\[([^\]]*)\]\(([^()\s]+)\)/g;
const WORD = /[A-Za-z0-9]/; // deliberately not \w: a trailing "_" is still part of "__bold__"
const SAFE_HREF = /^(?:https?:|mailto:)/i;
const BULLET = /^\s{0,3}([-*+]|\d+[.)])\s+(.*)$/;
const HEADING = /^\s{0,3}(#{1,6})\s+(.*)$/;
const QUOTE = /^\s{0,3}>\s?(.*)$/;
const FENCE = /^\s{0,3}```/;

function inline(text) {
  const out = [];
  let last = 0;
  let match;
  INLINE.lastIndex = 0;
  while ((match = INLINE.exec(text))) {
    const [whole, , code, starStrong, lineStrong, starEm, lineEm, strike, label, href] = match;
    // `snake_case` and `__init__` are far more likely in this app's chatter than
    // underscore emphasis, so only honour `_` when it isn't glued to a word.
    const underscore = lineStrong !== undefined || lineEm !== undefined;
    if (underscore && (WORD.test(text[match.index - 1] || '') || WORD.test(text[INLINE.lastIndex] || ''))) {
      INLINE.lastIndex = match.index + 1; // rescan: "a_b and __x__" still has real emphasis in it
      continue;
    }
    if (match.index > last) out.push(text.slice(last, match.index));
    // INLINE is a shared /g regex, so the recursive calls below reset its
    // lastIndex out from under this loop unless it is put back afterwards.
    const resume = INLINE.lastIndex;
    last = resume;
    const key = out.length;
    const strong = starStrong ?? lineStrong;
    const em = starEm ?? lineEm;
    if (code !== undefined) out.push(<code key={key}>{code.trim()}</code>);
    else if (strong !== undefined) out.push(<strong key={key}>{inline(strong)}</strong>);
    else if (em !== undefined) out.push(<em key={key}>{inline(em)}</em>);
    else if (strike !== undefined) out.push(<s key={key}>{inline(strike)}</s>);
    else if (SAFE_HREF.test(href)) out.push(<a key={key} href={href} target="_blank" rel="noreferrer noopener">{inline(label || href)}</a>);
    else out.push(whole); // javascript: and friends stay as plain text
    INLINE.lastIndex = resume;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

// Soft line breaks inside a paragraph are kept — panellists use them for beats.
function paragraph(lines, key) {
  const body = [];
  lines.forEach((line, index) => {
    if (index) body.push(<br key={`br${index}`} />);
    body.push(...inline(line));
  });
  return <p key={key}>{body}</p>;
}

function blocks(source) {
  const lines = source.replace(/\r\n?/g, '\n').split('\n');
  const nodes = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    const key = `b${index}`;
    if (!line.trim()) { index += 1; continue; }

    if (FENCE.test(line)) {
      const body = [];
      index += 1;
      while (index < lines.length && !FENCE.test(lines[index])) { body.push(lines[index]); index += 1; }
      index += 1; // the closing fence, or the end of an unterminated block
      nodes.push(<pre key={key}><code>{body.join('\n')}</code></pre>);
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading) {
      const Tag = `h${Math.min(heading[1].length + 2, 6)}`; // demoted: the panel owns h1/h2
      nodes.push(<Tag key={key}>{inline(heading[2])}</Tag>);
      index += 1;
      continue;
    }

    if (BULLET.test(line)) {
      const ordered = /^\s{0,3}\d/.test(line);
      const items = [];
      while (index < lines.length && BULLET.test(lines[index]) && /^\s{0,3}\d/.test(lines[index]) === ordered) {
        items.push(<li key={index}>{inline(BULLET.exec(lines[index])[2])}</li>);
        index += 1;
      }
      const List = ordered ? 'ol' : 'ul';
      nodes.push(<List key={key}>{items}</List>);
      continue;
    }

    if (QUOTE.test(line)) {
      const quoted = [];
      while (index < lines.length && QUOTE.test(lines[index])) { quoted.push(QUOTE.exec(lines[index])[1]); index += 1; }
      nodes.push(<blockquote key={key}>{paragraph(quoted, 'q')}</blockquote>);
      continue;
    }

    const run = [];
    while (index < lines.length && lines[index].trim() && !FENCE.test(lines[index])
      && !BULLET.test(lines[index]) && !HEADING.test(lines[index]) && !QUOTE.test(lines[index])) {
      run.push(lines[index]);
      index += 1;
    }
    nodes.push(paragraph(run, key));
  }
  return nodes;
}

export default function Markdown({ text }) {
  const nodes = blocks(String(text ?? ''));
  // One plain paragraph is the common case, and the transcript prefixes it with
  // "Name: " — so unwrap it and stay inline instead of breaking onto a new line.
  if (nodes.length === 1 && nodes[0].type === 'p') return <>{nodes[0].props.children}</>;
  return <>{nodes}</>;
}

/* Blog index (blog.html) and single post (blog-post.html?id=N), rendered from blog-posts.json.
 * Post bodies are trusted HTML authored in blog-posts.json; titles and tags are inserted as text. */
(function () {
  'use strict';
  const list = document.getElementById('blog-list');
  const article = document.getElementById('blog-post');
  if (!list && !article) return;

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const plain = html => { const d = document.createElement('div'); d.innerHTML = html.replace(/<(?=\/?(p|h\d|li|div|br|td|th|tr|pre)\b)/gi, ' <'); return (d.textContent || '').replace(/\s+/g, ' ').trim(); };
  const fmtDate = (iso, lang) => new Date(iso).toLocaleDateString(lang === 'ar' ? 'ar' : 'en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
  const minutes = html => Math.max(1, Math.round(plain(html).split(' ').length / 220));

  function meta(post) {
    const m = el('div', 'post-meta');
    m.append(el('span', null, fmtDate(post.date, post.lang)), el('span', null, minutes(post.content) + ' min read'));
    if (post.lang === 'ar') m.append(el('span', null, 'العربية'));
    return m;
  }
  function tags(post) {
    const t = el('div', 'project-tags');
    (post.tags || []).forEach(tag => t.append(el('span', 'project-tag', '#' + tag)));
    return t;
  }
  function fail(target, msg) { target.replaceChildren(el('p', 'c-muted', msg)); }

  fetch('blog-posts.json')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(posts => {
      if (list) {
        if (!posts.length) return fail(list, 'No posts yet.');
        const order = posts.map((p, i) => [p, i]).sort((a, b) => new Date(b[0].date) - new Date(a[0].date));
        list.replaceChildren(...order.map(([post, i], n) => {
          const a = el('a', 'blog-card' + (n === 0 ? ' blog-card-latest' : ''));
          a.href = 'blog-post.html?id=' + i;
          if (post.lang === 'ar') a.dir = 'rtl';
          const text = plain(post.content);
          a.append(
            el('div', 'blog-card-idx', (n === 0 ? 'latest · ' : '') + String(order.length - n).padStart(2, '0')),
            el('h2', 'blog-card-title', post.title),
            meta(post),
            el('p', 'blog-card-excerpt', text.length > 220 ? text.slice(0, 220).replace(/\s\S*$/, '') + '…' : text),
            tags(post),
            el('span', 'blog-card-more', 'read post →'),
          );
          return a;
        }));
      }
      if (article) {
        const id = parseInt(new URLSearchParams(location.search).get('id'), 10);
        const post = posts[id];
        if (!post) return fail(article, 'Post not found. Head back to the blog for the full list.');
        document.title = post.title + ' · Ziad Hares';
        article.dir = post.lang === 'ar' ? 'rtl' : 'ltr';
        if (post.lang === 'ar') article.lang = 'ar';
        const back = el('a', 'post-back', '← cd ../blog');
        back.href = 'blog.html';
        const head = el('header', 'post-head');
        head.append(back, el('h1', 'post-title', post.title), meta(post), tags(post));
        const body = el('div', 'prose');
        body.innerHTML = post.content;
        const end = el('a', 'btn btn-ghost post-end', '← back to all posts');
        end.href = 'blog.html';
        article.replaceChildren(head, body, end);
      }
    })
    .catch(() => fail(list || article, 'Could not load posts. Please try again later.'));
})();

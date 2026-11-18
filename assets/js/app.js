// Filtering for the home page. Everything is rendered by Hugo; this only shows and hides rows.
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const search = $("#q");
  if (!search) return; // text pages have no list

  const groups = $$(".group");
  const cats = $$(".cat");
  const subLinks = $$(".subcat");
  const subsLists = $$(".subs");
  const chips = $("#chips");
  const status = $("#status");
  const empty = $("#empty");
  const title = $("#title");
  const lede = $("#lede");
  const total = $$(".item").length;
  const state = { cat: "all", sub: "", q: "", filter: "all" };

  // The address is #category or #category/subcategory, so every view can be linked to.
  const readHash = () => {
    const [id, slug] = decodeURIComponent(location.hash.slice(1)).split("/");
    if (!groups.some((g) => g.dataset.cat === id)) return { cat: "all", sub: "" };
    const link = subLinks.find((a) => a.dataset.cat === id && a.dataset.slug === slug);
    return { cat: id, sub: link ? link.dataset.sub : "" };
  };

  // Narrow screens show the subcategories as a row of chips; wide screens in the sidebar.
  function renderChips() {
    const links = subLinks.filter((a) => a.dataset.cat === state.cat);
    if (!links.length) { chips.hidden = true; chips.replaceChildren(); return; }
    const button = (slug, label, n, pressed) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.dataset.slug = slug;
      b.setAttribute("aria-pressed", String(pressed));
      b.textContent = label;
      if (n) { const s = document.createElement("span"); s.className = "n"; s.textContent = n; b.append(s); }
      return b;
    };
    chips.replaceChildren(button("", "All", "", !state.sub),
      ...links.map((a) => button(a.dataset.slug, a.dataset.sub, $(".n", a).textContent, a.dataset.sub === state.sub)));
    chips.hidden = false;
  }

  function apply() {
    const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    groups.forEach((g) => {
      const inCat = state.cat === "all" || g.dataset.cat === state.cat;
      let n = 0;
      $$(".item", g).forEach((li) => {
        const ok = inCat &&
          (!state.sub || li.dataset.sub === state.sub) &&
          (state.filter === "all" || li.hasAttribute("data-" + state.filter)) &&
          terms.every((t) => li.dataset.s.includes(t));
        li.hidden = !ok;
        if (ok) n++;
      });
      $$(".subgroup", g).forEach((sg) => {
        const visible = $$(".item", sg).filter((li) => !li.hidden).length;
        sg.hidden = visible === 0;
        const c = $(".subcount", sg);
        if (c) c.textContent = visible;
      });
      g.hidden = n === 0;
      const count = $(".count", g);
      if (count) count.textContent = n;
      shown += n;
    });

    const group = groups.find((g) => g.dataset.cat === state.cat);
    title.textContent = state.q ? `Results for “${state.q}”` : group ? group.dataset.name : "All resources";
    lede.textContent = group && !state.q ? group.dataset.desc : lede.dataset.default;
    const narrowed = state.q || state.sub || state.filter !== "all" || state.cat !== "all";
    status.textContent = narrowed && shown ? `Showing ${shown} of ${total}` : "";
    empty.hidden = shown > 0;
    cats.forEach((a) => {
      a.setAttribute("aria-current", String(a.dataset.cat === state.cat && !state.sub));
      a.classList.toggle("open", a.dataset.cat === state.cat);
    });
    subsLists.forEach((l) => { l.hidden = l.dataset.for !== state.cat; });
    subLinks.forEach((a) => a.setAttribute("aria-current", String(a.dataset.cat === state.cat && a.dataset.sub === state.sub)));
  }

  function route() {
    Object.assign(state, readHash());
    renderChips();
    apply();
  }

  window.addEventListener("hashchange", () => { route(); window.scrollTo({ top: 0 }); });

  search.addEventListener("input", () => { state.q = search.value.trim(); apply(); });
  search.addEventListener("keydown", (e) => { if (e.key === "Escape") { search.value = ""; state.q = ""; apply(); search.blur(); } });

  chips.addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (b) location.hash = b.dataset.slug ? `${state.cat}/${b.dataset.slug}` : state.cat;
  });

  $$(".segmented button").forEach((b) => b.addEventListener("click", () => {
    state.filter = b.dataset.filter;
    $$(".segmented button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  }));

  document.addEventListener("keydown", (e) => {
    const typing = /^(input|textarea|select)$/i.test(document.activeElement?.tagName || "");
    if ((e.key === "/" && !typing) || (e.key.toLowerCase() === "k" && (e.metaKey || e.ctrlKey))) {
      e.preventDefault();
      search.focus();
      search.select();
    }
  });

  route();
})();

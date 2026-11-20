/* Qafila — interactions du site vitrine (aucune dépendance) */
(() => {
  "use strict";
  const doc = document.documentElement;
  doc.classList.add("js");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;

  /* ---------- Navigation ---------- */
  const nav = $(".nav");
  const toggle = $(".nav__toggle");
  const mobile = $("#menu-mobile");
  if (toggle && mobile) {
    const setMenu = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
      mobile.hidden = !open;
    };
    toggle.addEventListener("click", () => setMenu(toggle.getAttribute("aria-expanded") !== "true"));
    $$("a", mobile).forEach((a) => a.addEventListener("click", () => setMenu(false)));
  }
  const links = $$(".nav__links a");
  if ("IntersectionObserver" in window && links.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === `#${e.target.id}`));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    links.map((a) => $(a.getAttribute("href"))).filter(Boolean).forEach((s) => spy.observe(s));
  }

  /* ---------- Le voyage : décor piloté par le défilement ----------
     Chaque section porte data-scene (0 = Golfe de Tunis … 4 = nuit au Sahara).
     Performance : le décor est fait de calques SVG statiques ; on ne touche qu'à
     transform et opacity (composités par le GPU), jamais au contenu des SVG. */
  const VW = 1600, VH = 900;
  const SKY = [["#BCD2E6", "#F2F0E8"], ["#EFE2C4", "#F7F0E0"], ["#EBC88F", "#F5E3C3"], ["#C97A55", "#EDB98A"], ["#0B1222", "#16213A"]];
  const SUN = [[1180, 230], [1150, 190], [1100, 250], [1040, 560], [1000, 860]];
  const smooth = (t) => t * t * (3 - 2 * t);
  const pick = (arr, s) => {
    const i = Math.floor(clamp(s, 0, arr.length - 1.0001));
    const t = clamp(s - i);
    return arr[i].map((v, k) => lerp(v, arr[i + 1][k], t));
  };

  const art = $(".world__art");
  const rail = $(".rail");
  const stops = rail ? $$(".rail__stop", rail) : [];
  const railFill = rail && $(".rail__fill", rail);
  const railTruck = rail && $(".rail__truck", rail);
  let anchors = [];
  let geo = { scale: 1, left: 0, top: 0, railH: 0 };
  let world = null;
  let stage = -1;
  let night = null;

  const measure = () => {
    anchors = $$("[data-scene]").map((el) => {
      const r = el.getBoundingClientRect();
      const y = el.classList.contains("hero") ? window.innerHeight / 2 : r.top + window.scrollY + r.height / 2;
      return { y, s: parseFloat(el.dataset.scene) };
    }).sort((a, b) => a.y - b.y);
    const vw = window.innerWidth, vh = window.innerHeight;
    const scale = Math.max(vw / VW, vh / VH);
    geo = { scale, left: (vw - VW * scale) / 2, top: vh - VH * scale, railH: rail ? $(".rail__track", rail).offsetHeight : 0 };
    if (world) {
      world.actors.forEach((a) => {
        a.el.style.width = `${a.box[2] * scale}px`;
        a.el.style.height = `${a.box[3] * scale}px`;
      });
      world.orbs.forEach((o) => { o.el.style.width = o.el.style.height = `${o.size * scale}px`; });
    }
  };
  const px = (x, y) => [geo.left + x * geo.scale, geo.top + y * geo.scale];
  const move = (el, x, y) => { el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`; };

  const position = () => {
    if (!anchors.length) return 0;
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) return anchors[anchors.length - 1].s;
    const c = window.scrollY + window.innerHeight / 2;
    if (c <= anchors[0].y) return anchors[0].s;
    for (let i = 0; i < anchors.length - 1; i++) {
      const a = anchors[i], b = anchors[i + 1];
      if (c <= b.y) return lerp(a.s, b.s, (c - a.y) / Math.max(1, b.y - a.y));
    }
    return anchors[anchors.length - 1].s;
  };

  const render = () => {
    const s = position();
    if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 8);

    // réglages discrets (texte, barre de navigation) : seulement quand l'étape change
    const st = Math.round(s);
    if (st !== stage) {
      stage = st;
      doc.style.setProperty("--sky-top", SKY[st][0]);
      doc.style.setProperty("--halo", SKY[st][1]);
    }
    const isNight = s > 3.55;
    if (isNight !== night) { night = isNight; document.body.classList.toggle("is-night", isNight); }

    // route de progression
    if (rail) {
      const p = s / 4;
      if (railFill) railFill.style.transform = `scaleY(${p.toFixed(4)})`;
      if (railTruck) railTruck.style.transform = `translate3d(0, ${(p * geo.railH).toFixed(1)}px, 0)`;
      stops.forEach((el, i) => {
        el.classList.toggle("is-past", s >= i - .02);
        el.classList.toggle("is-here", Math.abs(s - i) < .5);
      });
    }
    if (!world) return;

    // ciel : 5 dégradés superposés, fondu continu
    const sb = Math.floor(clamp(s, 0, 3.9999));
    const sf = smooth(clamp(s - sb));
    world.skies.forEach((el, i) => { el.style.opacity = i < sb ? 0 : i === sb ? 1 : i === sb + 1 ? sf.toFixed(3) : 0; });

    // scènes : la courante reste pleine dessous, la suivante apparaît par-dessus
    const base = Math.floor(clamp(s, 0, world.scenes.length - 1));
    const fade = smooth(clamp((s - base - .38) / .3));
    world.scenes.forEach((sc, i) => {
      const live = i >= base - 1 && i <= base + 1;
      if (sc.live !== live) { sc.live = live; sc.el.style.visibility = live ? "visible" : "hidden"; }
      const op = i === base ? 1 : i === base + 1 ? fade : 0;
      if (sc.op !== op) { sc.op = op; sc.el.style.opacity = op.toFixed(3); }
      if (!live || op === 0) return;
      const d = s - i;
      sc.layers.forEach(({ el, depth }) => {
        move(el, reduceMotion ? 0 : -d * depth * 240 * geo.scale, reduceMotion ? 0 : Math.abs(d) * depth * 50 * geo.scale);
      });
      sc.actors.forEach((a) => {
        const dx = a.name === "truck" ? 980 + (s - 1) * 760 : (s - 3) * 300;
        const k = a.name === "truck" ? 1 : .55;
        const [x, y] = px(a.box[0] + dx, a.box[1]);
        move(a.el, x + (reduceMotion ? 0 : -d * k * 240 * geo.scale), y + (reduceMotion ? 0 : Math.abs(d) * k * 50 * geo.scale));
      });
    });

    // soleil, lune, étoiles, nuages
    const [sx, sy] = pick(SUN, s);
    const [ux, uy] = px(sx, sy);
    world.orbs.forEach((o) => {
      if (o.name === "sun") move(o.el, ux - o.size * geo.scale / 2, uy - o.size * geo.scale / 2);
    });
    const n = clamp((s - 3.2) / .7);
    const moon = world.orbs.find((o) => o.name === "moon");
    if (moon) {
      const [mx, my] = px(1230, 260 - n * 90);
      move(moon.el, mx - moon.size * geo.scale / 2, my - moon.size * geo.scale / 2);
      moon.el.style.opacity = n.toFixed(3);
    }
    if (world.stars) world.stars.style.opacity = n.toFixed(3);
    if (world.clouds) world.clouds.style.opacity = (1 - clamp((s - 1.8) / 1.3)).toFixed(3);
  };

  let queued = false;
  const onScroll = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; render(); });
  };
  measure();
  render();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => { measure(); onScroll(); });
  window.addEventListener("load", () => { measure(); onScroll(); });

  if (art && window.fetch) {
    fetch("/assets/img/world.html?v=4")
      .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
      .then((html) => {
        art.innerHTML = html;
        world = {
          skies: $$(".w-sky", art),
          stars: $(".w-stars", art),
          clouds: $(".w-clouds", art),
          orbs: [["sun", ".w-sun", 320], ["moon", ".w-moon", 200]]
            .map(([name, sel, size]) => ({ name, el: $(sel, art), size })).filter((o) => o.el),
          scenes: $$(".w-scene", art).map((el) => ({
            el,
            op: null,
            live: null,
            layers: $$(".w-layer", el).map((l) => ({ el: l, depth: parseFloat(l.dataset.depth) || 0 })),
            actors: $$(".w-actor", el).map((a) => ({
              el: a,
              name: a.classList.contains("w-truck") ? "truck" : "caravan",
              box: a.dataset.box.split(" ").map(Number),
            })),
          })),
        };
        world.actors = world.scenes.flatMap((sc) => sc.actors);
        document.body.classList.add("has-world");
        measure();
        render();
      })
      .catch(() => { /* le ciel par défaut reste affiché */ });
  }

  /* ---------- Carte : routes animées et camion ---------- */
  const routes = $$(".qf-map__route");
  const truck = $(".qf-map__truck");
  if (routes.length && truck) {
    if (!reduceMotion) {
      routes.forEach((r, i) => {
        r.animate([{ strokeDashoffset: 0 }, { strokeDashoffset: -26 }], { duration: 1600 + i * 200, iterations: Infinity });
      });
    }
    const coast = routes.find((r) => r.dataset.route === "cote") || routes[0];
    const len = coast.getTotalLength();
    const place = (p) => {
      const pt = coast.getPointAtLength(p * len);
      truck.setAttribute("cx", pt.x.toFixed(1));
      truck.setAttribute("cy", pt.y.toFixed(1));
    };
    if (reduceMotion) {
      place(0.55);
    } else {
      const period = 9000;
      const loop = (t) => {
        const p = (t % period) / period;
        place(p < 0.9 ? p / 0.9 : 1); // petite pause à l'arrivée
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
  }

  /* ---------- Suivi d'expédition ---------- */
  const trackForm = $("#track-form");
  const trackInput = $("#track-ref");
  const trackOut = $("#track-result");
  const REF = /^[A-Z]{2,5}\/[A-Z]{2,5}\/\d{1,6}$/;
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const showTrackError = (msg) => trackOut.replaceChildren(el("p", "track__error", msg));

  async function track(ref) {
    ref = ref.trim().toUpperCase();
    trackInput.value = ref;
    if (!REF.test(ref)) {
      showTrackError("Format attendu : trois blocs, par exemple QRD/OUT/00003.");
      trackInput.focus();
      return;
    }
    const btn = $("button[type=submit]", trackForm);
    btn.disabled = true;
    trackOut.replaceChildren(el("p", "track__empty", "Recherche en cours…"));
    try {
      const res = await fetch(`/api/suivi?ref=${encodeURIComponent(ref)}`, { headers: { Accept: "application/json" } });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        showTrackError(data.error || "Service de suivi momentanément indisponible.");
        return;
      }
      const list = el("ol", "steps");
      data.etapes.forEach((s) => {
        const li = el("li", s.fait ? "is-done" : "", s.libelle);
        if (s.code === data.etape) {
          li.classList.add("is-current");
          li.setAttribute("aria-current", "step");
          if (s.code === "livre") li.classList.add("is-final");
        }
        list.append(li);
      });
      const route = [data.depart, data.destination].filter(Boolean).join(" → ");
      trackOut.replaceChildren(
        el("p", "track__ref", data.reference),
        el("p", "track__title", data.libelle),
        el("p", "track__meta", [route, data.date && `${data.date_label} ${data.date}`, data.vehicule && `Camion ${data.vehicule}`].filter(Boolean).join(" · ")),
        list,
      );
    } catch (err) {
      showTrackError("Connexion impossible au service de suivi. Réessayez dans un instant.");
    } finally {
      btn.disabled = false;
    }
  }
  if (trackForm) {
    trackForm.addEventListener("submit", (e) => {
      e.preventDefault();
      track(trackInput.value);
    });
    $$("[data-ref]").forEach((b) => b.addEventListener("click", () => track(b.dataset.ref)));
  }

  /* ---------- Demande de devis ---------- */
  const form = $("#devis-form");
  const status = $("#devis-status");
  const EMAIL = /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i;
  const setStatus = (msg, kind) => {
    status.textContent = msg;
    status.className = `form__status${kind ? ` is-${kind}` : ""}`;
  };
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(form).entries());
      const nom = form.elements.nom;
      const email = form.elements.email;
      nom.setAttribute("aria-invalid", String(data.nom.trim().length < 2));
      email.setAttribute("aria-invalid", String(!EMAIL.test(data.email.trim())));
      if (data.nom.trim().length < 2) { setStatus("Merci d'indiquer votre nom.", "error"); nom.focus(); return; }
      if (!EMAIL.test(data.email.trim())) { setStatus("Adresse e-mail invalide.", "error"); email.focus(); return; }

      const btn = $("button[type=submit]", form);
      btn.disabled = true;
      setStatus("Envoi en cours…");
      try {
        const res = await fetch("/api/devis", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(data),
        });
        const out = await res.json().catch(() => ({}));
        if (!res.ok || !out.ok) {
          setStatus(out.error || "Envoi impossible pour le moment. Réessayez plus tard.", "error");
          return;
        }
        form.reset();
        setStatus(out.reference
          ? `Merci ! Demande ${out.reference} enregistrée, nous revenons vers vous sous un jour ouvré.`
          : "Merci ! Votre demande est enregistrée.", "ok");
      } catch (err) {
        setStatus("Connexion impossible. Vérifiez votre réseau et réessayez.", "error");
      } finally {
        btn.disabled = false;
      }
    });
  }
})();

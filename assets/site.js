(() => {
  "use strict";

  const visualization = document.querySelector(".task-list");
  const cards = Array.from(visualization.querySelectorAll(".task-card"));
  const picker = document.querySelector("#robotwin .task-picker");
  const taskButtons = Array.from(picker.querySelectorAll("button"));
  const announcement = document.querySelector("#task-announcement");
  const navLinks = Array.from(document.querySelectorAll(".section-nav a"));
  const sections = navLinks.map(link => document.querySelector(link.hash));
  const progress = document.querySelector(".scroll-progress");
  let activeIndex = -1;
  let navigationFrame = false;

  function updateNavigation() {
    navigationFrame = false;
    const scrollableHeight = document.documentElement.scrollHeight - window.innerHeight;
    const fraction = scrollableHeight > 0 ? window.scrollY / scrollableHeight : 0;
    progress.style.transform = `scaleX(${Math.min(1, Math.max(0, fraction))})`;
    let activeSection = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= window.innerHeight * 0.35) activeSection = section;
    }
    for (const link of navLinks) {
      if (link.hash === `#${activeSection.id}`) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    }
  }

  function scheduleNavigationUpdate() {
    if (navigationFrame) return;
    navigationFrame = true;
    window.requestAnimationFrame(updateNavigation);
  }

  function selectTask(index, announce = true) {
    if (index === activeIndex) return;
    cards.forEach((card, i) => {
      const selected = i === index;
      const video = card.querySelector("video");
      card.hidden = !selected;
      if (!selected) video.pause();
      else if (video.readyState >= 1) video.currentTime = 0;
      taskButtons[i].classList.toggle("active", selected);
      taskButtons[i].setAttribute("aria-pressed", String(selected));
    });
    activeIndex = index;
    if (announce) announcement.textContent = `${taskButtons[index].textContent}: visualization and success-rate curve selected.`;
  }

  taskButtons.forEach((button, index) => button.addEventListener("click", () => {
    selectTask(index);
    const hash = `#${cards[index].id}`;
    if (window.location.hash !== hash) window.history.pushState(null, "", hash);
  }));
  picker.hidden = false;

  function navigateTasks(event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const destinations = { ArrowLeft: activeIndex - 1, ArrowRight: activeIndex + 1, Home: 0, End: cards.length - 1 };
    if (!Object.prototype.hasOwnProperty.call(destinations, event.key)) return;
    event.preventDefault();
    const index = Math.max(0, Math.min(cards.length - 1, destinations[event.key]));
    taskButtons[index].click();
    if (event.currentTarget === picker) taskButtons[index].focus({ preventScroll: true });
  }
  picker.addEventListener("keydown", navigateTasks);
  visualization.addEventListener("keydown", event => {
    if (event.target === visualization) navigateTasks(event);
  });

  function revealHashTarget() {
    const index = cards.findIndex(card => `#${card.id}` === window.location.hash);
    if (index < 0) return;
    selectTask(index);
    visualization.scrollIntoView({ block: "start", behavior: "auto" });
  }
  window.addEventListener("hashchange", revealHashTarget);
  window.addEventListener("popstate", revealHashTarget);

  const videoVisibility = new IntersectionObserver(entries => {
    entries.forEach(entry => { if (!entry.isIntersecting) entry.target.pause(); });
  });
  document.querySelectorAll("video").forEach(video => videoVisibility.observe(video));
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) document.querySelectorAll("video").forEach(video => video.pause());
  });

  window.addEventListener("scroll", scheduleNavigationUpdate, { passive: true });
  window.addEventListener("resize", scheduleNavigationUpdate);
  window.addEventListener("load", () => { revealHashTarget(); scheduleNavigationUpdate(); });
  selectTask(0, false);
  revealHashTarget();
  updateNavigation();
})();

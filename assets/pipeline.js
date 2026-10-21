(() => {
  "use strict";

  function initializeTaskPicker(pickerSelector, panelSelector, announcementSelector, label) {
    const picker = document.querySelector(pickerSelector);
    if (!picker) return;
    const buttons = Array.from(picker.querySelectorAll("button"));
    const panels = Array.from(document.querySelectorAll(panelSelector));
    const announcement = document.querySelector(announcementSelector);
    let activeIndex = -1;

    function selectTask(index, announce = true) {
      if (index === activeIndex) return;
      panels.forEach((panel, i) => {
        const selected = i === index;
        panel.hidden = !selected;
        panel.querySelectorAll("video").forEach(video => {
          if (!selected) video.pause();
          else if (video.readyState >= 1) video.currentTime = 0;
        });
        buttons[i].classList.toggle("active", selected);
        buttons[i].setAttribute("aria-pressed", String(selected));
      });
      activeIndex = index;
      if (announce) announcement.textContent = `${buttons[index].textContent}: ${label} video selected.`;
    }

    buttons.forEach((button, index) => button.addEventListener("click", () => selectTask(index)));
    picker.addEventListener("keydown", event => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const destinations = { ArrowLeft: activeIndex - 1, ArrowRight: activeIndex + 1, Home: 0, End: panels.length - 1 };
      if (!Object.prototype.hasOwnProperty.call(destinations, event.key)) return;
      event.preventDefault();
      const index = Math.max(0, Math.min(panels.length - 1, destinations[event.key]));
      selectTask(index);
      buttons[index].focus({ preventScroll: true });
    });

    selectTask(0, false);
    picker.hidden = false;
  }

  initializeTaskPicker("#data-generation .pipeline-picker", "#data-generation .pipeline-video", "#pipeline-announcement", "Agentic Keypoint Programs");
  initializeTaskPicker("#corrective-data-generation .detection-picker", "#corrective-data-generation .detection-task", "#detection-announcement", "Policy Failure Detection and Correction");
  initializeTaskPicker("#corrective-data-generation .iterations-picker", "#corrective-data-generation .automatic-corrections-video", "#iterations-announcement", "Policy Improvement");
  initializeTaskPicker("#sim-to-real .domain-randomization-picker", "#sim-to-real .domain-randomization-video", "#domain-randomization-announcement", "Domain Randomization");
})();

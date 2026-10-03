document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-video-switcher]").forEach((switcher) => {
    const frame = switcher.querySelector(".behavior-video-frame");
    const prompt = switcher.querySelector("[data-behavior-prompt]");
    const primaryVideo = frame.querySelector("video");
    const secondaryVideo = primaryVideo.cloneNode(true);
    const secondarySource = secondaryVideo.querySelector("source");
    const buttons = Array.from(switcher.querySelectorAll("[data-video-src]"));
    let activeVideo = primaryVideo;
    let changeId = 0;

    primaryVideo.classList.add("is-visible");
    secondaryVideo.removeAttribute("autoplay");
    secondarySource.removeAttribute("src");
    frame.appendChild(secondaryVideo);

    const revealVideo = (nextVideo, requestId) => {
      if (requestId !== changeId) return;
      const previousVideo = activeVideo;
      nextVideo.muted = true;
      nextVideo.play().catch(() => {});
      nextVideo.classList.add("is-visible");
      previousVideo.classList.remove("is-visible");
      activeVideo = nextVideo;
      window.setTimeout(() => previousVideo.pause(), 300);
    };

    const selectVideo = (button, isInitial = false) => {
      buttons.forEach((candidate) => {
        const isActive = candidate === button;
        candidate.classList.toggle("is-active", isActive);
        candidate.setAttribute("aria-selected", String(isActive));
      });
      prompt.textContent = button.dataset.prompt;

      const nextSource = button.dataset.videoSrc;
      const currentSource = activeVideo.querySelector("source").getAttribute("src");
      if (isInitial || currentSource === nextSource) {
        activeVideo.muted = true;
        activeVideo.play().catch(() => {});
        return;
      }

      const requestId = ++changeId;
      const nextVideo = Array.from(frame.querySelectorAll("video")).find(
        (candidate) => candidate !== activeVideo
      );
      const source = nextVideo.querySelector("source");
      nextVideo.classList.remove("is-visible");
      source.setAttribute("src", nextSource);
      nextVideo.load();

      if (nextVideo.readyState >= 2) {
        revealVideo(nextVideo, requestId);
      } else {
        nextVideo.addEventListener(
          "loadeddata",
          () => revealVideo(nextVideo, requestId),
          { once: true }
        );
      }
    };

    buttons.forEach((button) => {
      button.addEventListener("click", () => selectVideo(button));
    });

    selectVideo(buttons[0], true);
  });
});

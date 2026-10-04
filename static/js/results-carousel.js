document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-results-carousel]").forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll("[data-slide]"));
    const viewport = carousel.querySelector(".carousel-slides");
    const previousButton = carousel.querySelector(".carousel-arrow-prev");
    const nextButton = carousel.querySelector(".carousel-arrow-next");
    const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
    const track = document.createElement("div");
    let activeIndex = 0;
    let direction = 0;
    let isAnimating = false;

    track.className = "carousel-track";
    slides.forEach((slide) => {
      slide.hidden = false;
      track.appendChild(slide);
    });
    viewport.appendChild(track);

    const setTrackPosition = (percent, animate = true) => {
      track.classList.toggle("is-jumping", !animate);
      track.style.transform = `translateX(${percent}%)`;

      if (!animate) {
        void track.offsetWidth;
        requestAnimationFrame(() => track.classList.remove("is-jumping"));
      }
    };

    const setPlayingSlides = (playingSlides) => {
      Array.from(track.children).forEach((slide) => {
        const shouldPlay = playingSlides.includes(slide);
        slide.querySelectorAll("video").forEach((video) => {
          if (shouldPlay) {
            video.muted = true;
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      });
    };

    const updateIndicators = () => {
      slides.forEach((slide, index) => {
        const isActive = index === activeIndex;
        slide.classList.toggle("is-active", isActive);
        slide.setAttribute("aria-hidden", String(!isActive));
      });

      dots.forEach((dot, index) => {
        const isActive = index === activeIndex;
        dot.classList.toggle("is-active", isActive);
        dot.setAttribute("aria-current", isActive ? "true" : "false");
      });
    };

    const finishTransition = () => {
      if (!isAnimating) return;

      if (direction === 1) {
        track.appendChild(track.firstElementChild);
      }

      setTrackPosition(0, false);
      direction = 0;
      isAnimating = false;
      updateIndicators();
      setPlayingSlides([track.firstElementChild]);
    };

    const moveBy = (delta) => {
      if (isAnimating || !delta) return;
      isAnimating = true;
      direction = delta > 0 ? 1 : -1;
      activeIndex = (activeIndex + direction + slides.length) % slides.length;

      if (direction === 1) {
        const currentSlide = track.children[0];
        const incomingSlide = track.children[1];
        setPlayingSlides([currentSlide, incomingSlide]);
        setTrackPosition(-100, true);
      } else {
        const currentSlide = track.children[0];
        const incomingSlide = track.lastElementChild;
        track.insertBefore(incomingSlide, currentSlide);
        setTrackPosition(-100, false);
        setPlayingSlides([incomingSlide, currentSlide]);
        requestAnimationFrame(() => {
          requestAnimationFrame(() => setTrackPosition(0, true));
        });
      }

      updateIndicators();
      window.setTimeout(() => {
        if (isAnimating) finishTransition();
      }, 600);
    };

    const moveTo = (nextIndex) => {
      let delta = nextIndex - activeIndex;
      if (delta > slides.length / 2) delta -= slides.length;
      if (delta < -slides.length / 2) delta += slides.length;
      moveBy(delta);
    };

    track.addEventListener("transitionend", (event) => {
      if (event.target !== track || event.propertyName !== "transform") return;
      finishTransition();
    });

    previousButton.addEventListener("click", () => moveBy(-1));
    nextButton.addEventListener("click", () => moveBy(1));
    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => moveTo(index));
    });

    carousel.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") moveBy(-1);
      if (event.key === "ArrowRight") moveBy(1);
    });

    setTrackPosition(0, false);
    updateIndicators();
    setPlayingSlides([track.firstElementChild]);
  });
});

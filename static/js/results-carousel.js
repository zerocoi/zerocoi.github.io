document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-results-carousel]").forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll("[data-slide]"));
    const viewport = carousel.querySelector(".carousel-slides");
    const previousButton = carousel.querySelector(".carousel-arrow-prev");
    const nextButton = carousel.querySelector(".carousel-arrow-next");
    const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
    const track = document.createElement("div");
    let activeIndex = 0;

    track.className = "carousel-track";
    slides.forEach((slide) => {
      slide.hidden = false;
      track.appendChild(slide);
    });
    viewport.appendChild(track);

    const updateCarousel = (nextIndex) => {
      activeIndex = (nextIndex + slides.length) % slides.length;
      track.style.transform = `translateX(-${activeIndex * 100}%)`;

      slides.forEach((slide, index) => {
        const isActive = index === activeIndex;
        slide.classList.toggle("is-active", isActive);
        slide.setAttribute("aria-hidden", String(!isActive));

        slide.querySelectorAll("video").forEach((video) => {
          if (isActive) {
            video.muted = true;
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      });

      dots.forEach((dot, index) => {
        const isActive = index === activeIndex;
        dot.classList.toggle("is-active", isActive);
        dot.setAttribute("aria-current", isActive ? "true" : "false");
      });
    };

    previousButton.addEventListener("click", () => updateCarousel(activeIndex - 1));
    nextButton.addEventListener("click", () => updateCarousel(activeIndex + 1));
    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => updateCarousel(index));
    });

    carousel.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") updateCarousel(activeIndex - 1);
      if (event.key === "ArrowRight") updateCarousel(activeIndex + 1);
    });

    updateCarousel(0);
  });
});

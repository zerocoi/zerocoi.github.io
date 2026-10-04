document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector("[data-copy-bibtex]");
  const citation = document.querySelector("#bibtex-code");
  const label = button?.querySelector("[data-copy-label]");

  if (!button || !citation || !label) return;

  let resetTimer;

  const setCopiedState = () => {
    window.clearTimeout(resetTimer);
    button.classList.add("is-copied");
    label.textContent = "Copied";
    button.setAttribute("aria-label", "BibTeX citation copied");

    resetTimer = window.setTimeout(() => {
      button.classList.remove("is-copied");
      label.textContent = "Copy";
      button.setAttribute("aria-label", "Copy BibTeX citation");
    }, 3000);
  };

  const copyWithFallback = () => {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(citation);
    selection.removeAllRanges();
    selection.addRange(range);
    const succeeded = document.execCommand("copy");
    selection.removeAllRanges();
    if (!succeeded) throw new Error("Copy command failed");
  };

  const copyCitation = async (text) => {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (_) {
        // Some embedded browsers expose the Clipboard API without granting write access.
      }
    }

    copyWithFallback();
  };

  button.addEventListener("click", async () => {
    try {
      const text = citation.textContent.trim();
      await copyCitation(text);
      setCopiedState();
    } catch (_) {
      label.textContent = "Select text";
      button.setAttribute("aria-label", "Select the BibTeX citation to copy it manually");
    }
  });
});

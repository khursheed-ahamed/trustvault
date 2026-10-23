document.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest("[data-password-toggle]");
  if (!button) return;

  const input = document.getElementById(button.getAttribute("aria-controls"));
  if (!(input instanceof HTMLInputElement)) {
    throw new Error("Password visibility control is missing its input.");
  }

  const shouldShow = input.type === "password";
  input.type = shouldShow ? "text" : "password";
  button.setAttribute("aria-pressed", String(shouldShow));
  button.setAttribute("aria-label", `${shouldShow ? "Hide" : "Show"} password`);
});

const uploadForm = document.querySelector("[data-upload-form]");
if (uploadForm) {
  const input = uploadForm.querySelector("[data-file-input]");
  const dropzone = uploadForm.querySelector("[data-dropzone]");
  const strip = uploadForm.querySelector("[data-preview-strip]");
  const preview = () => {
    strip.replaceChildren();
    Array.from(input.files).forEach((file) => {
      if (!file.type.startsWith("image/")) return;
      const image = document.createElement("img");
      image.src = URL.createObjectURL(file);
      image.alt = file.name;
      strip.appendChild(image);
    });
  };
  input.addEventListener("change", preview);
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
  }));
  dropzone.addEventListener("drop", (event) => {
    input.files = event.dataTransfer.files;
    preview();
  });
}


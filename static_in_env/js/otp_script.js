document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(".input-field input");
  const button = document.querySelector("button");

  inputs.forEach((input, index) => {
    input.addEventListener("input", (e) => {
      const currentInput = e.target;
      const nextInput = currentInput.nextElementSibling;
      const prevInput = currentInput.previousElementSibling;

      // Eğer giriş değeri varsa ve bir sonraki input alanı varsa
      if (currentInput.value.length === 1 && nextInput) {
        nextInput.removeAttribute("disabled");
        nextInput.focus();
      }

      // Eğer mevcut input alanı boşsa ve geri tuşuna basıldıysa
      if (e.inputType === 'deleteContentBackward' && prevInput) {
        prevInput.removeAttribute("disabled");
        prevInput.focus();
      }

      // Butonu aktif hale getir
      const allFilled = Array.from(inputs).every(input => input.value.length > 0);
      button.classList.toggle("active", allFilled);
    });
  });

  // İlk inputa odaklan
  inputs[0].focus();
});

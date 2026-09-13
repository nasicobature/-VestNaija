const amountInput = document.querySelector(".amount-form input[name='amount']");
document.querySelectorAll("[data-amount]").forEach((button) => {
  button.addEventListener("click", () => {
    if (amountInput) amountInput.value = button.dataset.amount;
  });
});

const password = document.querySelector("input[name='password']");
const meter = document.querySelector("#strength");
if (password && meter) {
  password.addEventListener("input", () => {
    const value = password.value;
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/[0-9]/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    meter.value = score;
  });
}

const canvas = document.querySelector("#portfolioChart");
if (canvas) {
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 640;
  const height = 260;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  canvas.style.height = `${height}px`;
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#0f6b4f";
  ctx.lineWidth = 4;
  ctx.beginPath();
  const points = [180, 154, 166, 126, 136, 92, 108, 58];
  points.forEach((point, index) => {
    const x = 24 + index * ((width - 48) / (points.length - 1));
    if (index === 0) ctx.moveTo(x, point);
    else ctx.lineTo(x, point);
  });
  ctx.stroke();
  ctx.fillStyle = "rgba(15, 107, 79, .12)";
  ctx.lineTo(width - 24, height - 24);
  ctx.lineTo(24, height - 24);
  ctx.closePath();
  ctx.fill();
}

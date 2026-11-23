function setCircularProgress(meter) {
    const value = parseFloat(meter.getAttribute("data-value")) || 0;
    const type = meter.getAttribute("data-type") || "confidence";
    const fill = meter.querySelector(".progress-fill");
    const radius = fill.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;

    fill.style.strokeDasharray = circumference;
    fill.style.strokeDashoffset = circumference;

    setTimeout(function () {
        const offset = circumference - (value / 100) * circumference;
        fill.style.strokeDashoffset = offset;

        // Color based on value and type.
        if (type === "preparation") {
            if (value < 40) {
                fill.style.stroke = "#e74c3c";
            } else if (value < 75) {
                fill.style.stroke = "#9b59b6";
            } else {
                fill.style.stroke = "#2980b9";
            }
        } else {
            if (value < 40) {
                fill.style.stroke = "#e74c3c";
            } else if (value < 75) {
                fill.style.stroke = "#f39c12";
            } else {
                fill.style.stroke = "#27ae60";
            }
        }
    }, 100);
}

function updateLinearBar(slider, barId) {
    const bar = document.getElementById(barId);
    if (bar) {
        bar.style.width = slider.value + "%";
    }
}

function rotateAffirmation() {
    const banner = document.getElementById("affirmation-banner");
    const text = document.getElementById("affirmation-text");
    if (!banner || !text) return;

    const affirmations = JSON.parse(banner.getAttribute("data-affirmations") || "[]");
    if (affirmations.length === 0) return;

    const current = text.textContent.trim();
    let nextIndex = Math.floor(Math.random() * affirmations.length);
    // Try to pick a different affirmation than the current one.
    if (affirmations.length > 1) {
        while (affirmations[nextIndex] === current) {
            nextIndex = Math.floor(Math.random() * affirmations.length);
        }
    }

    text.style.opacity = "0";
    setTimeout(function () {
        text.textContent = affirmations[nextIndex];
        text.style.opacity = "1";
    }, 300);
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".circular-progress").forEach(setCircularProgress);

    // Update output values next to sliders on input.
    document.querySelectorAll(".confidence-slider").forEach(function (slider) {
        slider.addEventListener("input", function () {
            const output = this.nextElementSibling;
            if (output) {
                output.textContent = this.value + "%";
            }
        });
    });

    // Rotate affirmation every 5 minutes while the page is open.
    const banner = document.getElementById("affirmation-banner");
    if (banner) {
        const interval = parseInt(banner.getAttribute("data-interval"), 10) || 300000;
        setInterval(rotateAffirmation, interval);
    }
});

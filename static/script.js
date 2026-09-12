/* Vorschau/Download + Live-Tausch der Photos.
 * Die Foto-Chips liegen als Overlay über den Default-Fotos auf Seite 1 und tragen
 * die Upload-/Zoom/Verschiebungs-Logik. Transform-Werte werden live an das
 * Formular übergeben, damit sie bei Vorschau UND Download eingeflochten werden. */

function setBusy(btn, busy) {
    if (!btn) return;
    var orig =
        btn.getAttribute("data-label") ||
        ((btn.textContent = btn.textContent), btn.getAttribute("data-label"));
    if (orig === null || orig === undefined)
        btn.setAttribute("data-label", btn.textContent);
    btn.disabled = busy;
    btn.textContent = busy
        ? "⏳  Wird generiert …"
        : btn.getAttribute("data-label");
}

function makeHandler(action) {
    return function (event) {
        event.preventDefault();

        var form = document.getElementById("flyerForm");
        var previewBox = document.getElementById("previewBox");
        previewBox.style.display = "none";
        previewBox.innerHTML = "";

        var btn =
            action === "preview"
                ? document.getElementById("previewBtn")
                : document.getElementById("downloadBtn");
        setBusy(btn, true);

        // Neue FormData-Kopie anlegen, damit das Formular-Element nicht
        // durch ein persistierendes pages-Feld verschutzt wird.
        var fd = new FormData(form);
        fd.set("pages", "");

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/" + action);
        xhr.send(fd);

        xhr.onload = function () {
            setBusy(btn, false);
            if (action === "preview") {
                previewBox.innerHTML = xhr.responseText;
                previewBox.style.display = "block";
                buildOverlays();
            }
        };
        xhr.onerror = function () {
            setBusy(btn, false);
            previewBox.innerHTML =
                '<p style="color:#d02825;">Fehler beim Generieren. Bitte erneut versuchen.</p>';
            previewBox.style.display = "block";
        };
    };
}

// ---- Foto-Overlays in der Vorschau (Seite 1) ---------------------------------
var SLOT_STATE = {}; // slot -> { x, y, z, uploaded }
function st(slot) {
    return (
        SLOT_STATE[slot] ||
        (SLOT_STATE[slot] = { x: 0, y: 0, z: 1, uploaded: false })
    );
}
function setField(name, value) {
    var el = document.getElementById(name);
    if (el) el.value = value;
}

// Debounced Live-Neu-Render nach jeder Verschiebung/Zoom-Änderung.
var postTimer = null;
function previewPost() {
    clearTimeout(postTimer);
    postTimer = setTimeout(function () {
        doPreviewPost();
    }, 450);
}
function doPreviewPost() {
    var form = document.getElementById("flyerForm");
    if (!form) return;
    var fd = new FormData(form);
    fd.set("pages", "1"); // nur Innenseite (alle drei Photos dort)
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/preview");
    xhr.send(fd);
    xhr.onload = function () {
        var pb = document.getElementById("previewBox");
        if (xhr.status === 200) {
            pb.innerHTML = xhr.responseText;
            pb.style.display = "block";
            buildOverlays();
        } else {
            pb.innerHTML =
                '<p style="color:#d02825;">Fehler beim Generieren. Bitte erneut versuchen.</p>';
            pb.style.display = "block";
        }
    };
}

// Liest die zuletzt gesicherten Transform-Werte (Verschiebung/Zoom) für ein
// hochgeladenes Foto, damit die Knöpfe nach dem Neuloaden am richtigen Stand anfangen.
function seedTransform(slot) {
    var getNum = function (suffix) {
        var el = document.getElementById("tr-" + slot + "-" + suffix);
        return el ? parseFloat(el.value) : 0;
    };
    var t = { x: getNum("x"), y: getNum("y"), z: getNum("z") };
    if (!t.z) t.z = 1;
    SLOT_STATE[slot] = {
        x: t.x,
        y: t.y,
        z: t.z,
        uploaded: (SLOT_STATE[slot] && SLOT_STATE[slot].uploaded) || false,
    };
}

// Schreibt die aktuelle Verschiebung/Zoom in das Formular und triggert live Neu-Render.
function applyTransform(slot) {
    var b = st(slot);
    setField("tr-" + slot + "-x", b.x.toFixed(1));
    setField("tr-" + slot + "-y", b.y.toFixed(1));
    setField("tr-" + slot + "-z", b.z.toFixed(2));
    previewPost();
}

// Overlay-Chip je Slot über dem jeweiligen Foto auf Seite 1 bauen.
// Der Chip bleibt immer an Ort und Stelle; nur der Inhalt ändert sich:
// ohne eigenes Bild „📷 Eigenes Foto", sonst zwei Zoom-Knäufe (+/-).
function buildOverlays() {
    var wrap = document.querySelector('.page-wrap[data-page="1"]');
    if (!wrap) return;
    var img = wrap.querySelector("img");
    // Alte Overlays entfernen, damit sich keine Handler ansammeln.
    wrap.querySelectorAll(".photo-overlay").forEach(function (o) {
        o.remove();
    });
    var slots = JSON.parse(wrap.getAttribute("data-slots") || "[]");
    slots.forEach(function (box) {
        var slot = box.name;
        seedTransform(slot);

        var overlay = document.createElement("div");
        overlay.className = "photo-overlay";
        overlay.style.left = box.cx - box.w / 2 + "%";
        overlay.style.top = box.cy - box.h / 2 + "%";
        overlay.style.width = box.w + "%";
        overlay.style.height = box.h + "%";

        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "photo-chip";
        chip.setAttribute("data-slot", slot);

        if (SLOT_STATE[slot].uploaded) {
            // Statt „📷 Eigenes Foto" nur noch Zoom-Knäufe (+/-) im Chip.
            // var up = document.createElement("button");
            // var down = document.createElement("button");
            // var left = document.createElement("button");
            // var right = document.createElement("button");
            var minus = document.createElement("button");
            var plus = document.createElement("button");
            minus.type = "button";
            minus.className = "photo-zoom-btn photo-minus";
            minus.textContent = "-";
            minus.addEventListener("click", function (e) {
                e.stopPropagation();
                var b = st(slot);
                if (b.z < 0.5) b.z = 0.5;
                else b.z -= 0.1;
                if (b.z < 0.5) b.z = 0.5;
                applyTransform(slot);
            });
            plus.type = "button";
            plus.className = "photo-zoom-btn photo-plus";
            plus.textContent = "+";
            plus.addEventListener("click", function (e) {
                e.stopPropagation();
                var b = st(slot);
                if (b.z > 4) b.z = 4;
                else b.z += 0.1;
                if (b.z > 4) b.z = 4;
                applyTransform(slot);
            });
            chip.appendChild(minus);
            chip.appendChild(plus);
        } else {
            chip.textContent = "\uD83D\uDCF7 Eigenes Foto";
            chip.addEventListener("click", function (e) {
                e.stopPropagation();
                var input = document.getElementById(slot);
                if (input) {
                    input.value = "";
                    input.click();
                }
            });
        }
        overlay.appendChild(chip);
        img.parentNode.insertBefore(overlay, img);
    });
}

// Die (versteckten) Datei-Eingaben liegen im Formular, damit das gewählte
// Foto mit dem nächsten Preview-POST an den Server gesendet wird. Nach dem
// Hochladen wird die Vorschau neu gebaut, dann enthält der Chip die Knöpfe.
["woelflingo", "pfadi", "raider"].forEach(function (slot) {
    var inp = document.getElementById(slot);
    if (inp) {
        inp.addEventListener("change", function () {
            st(slot).uploaded = true;
            previewPost();
        });
    }
});

document
    .getElementById("previewBtn")
    .addEventListener("click", makeHandler("preview"));
document
    .getElementById("downloadBtn")
    .addEventListener("click", makeHandler("download"));

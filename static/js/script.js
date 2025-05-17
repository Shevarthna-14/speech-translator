let mediaRecorder;
let audioChunks = [];

const audioPreview = document.getElementById("audio-preview");
const translatedAudio = document.getElementById("translated-audio");
const status = document.getElementById("upload-status");
const startBtn = document.getElementById("start-record-btn");
const stopBtn = document.getElementById("stop-record-btn");
const uploadBtn = document.getElementById("upload-btn");
const audioUpload = document.getElementById("audio-upload");
const translateBtn = document.getElementById("translate-btn");
const languageSelect = document.getElementById("language");
const historyLog = document.getElementById("history-log");

// Upload audio file handler
uploadBtn.addEventListener("click", () => {
  const file = audioUpload.files[0];
  if (!file) {
    status.textContent = "Please select an audio file to upload.";
    return;
  }

  const formData = new FormData();
  formData.append("audio", file);

  fetch("/upload_audio", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      status.textContent = data.error;
      return;
    }
    status.textContent = data.message;
    audioPreview.src = data.path;
    audioPreview.style.display = "block";
    audioPreview.dataset.relpath = data.relative_path;
    audioPreview.load();
  })
  .catch(() => {
    status.textContent = "Upload failed!";
  });
});

// Start recording
startBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.start();

    status.textContent = "Recording...";
    startBtn.style.display = "none";
    stopBtn.style.display = "inline";

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      const arrayBuffer = await audioBlob.arrayBuffer();

      fetch("/record_audio", {
        method: "POST",
        body: arrayBuffer,
        headers: { "Content-Type": "application/octet-stream" }
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          status.textContent = data.error;
          return;
        }
        status.textContent = data.message;
        audioPreview.src = data.path;
        audioPreview.style.display = "block";
        audioPreview.dataset.relpath = data.relative_path;
        audioPreview.load();
      })
      .catch(() => {
        status.textContent = "Recording failed!";
      });

      startBtn.style.display = "inline";
      stopBtn.style.display = "none";
    };
  } catch (err) {
    status.textContent = "Microphone access denied or error occurred.";
    console.error(err);
  }
});

// Stop recording
stopBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    status.textContent = "Saving recording...";
  }
});

// Translate audio
translateBtn.addEventListener("click", () => {
  const lang = languageSelect.value;
  const audioRelPath = audioPreview.dataset.relpath;

  if (!audioRelPath || audioRelPath.trim() === "") {
    alert("Please upload or record audio before translating.");
    return;
  }

  fetch("/translate_audio", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audio_path: audioRelPath,
      target_language: lang
    })
  })
  .then(response => {
    if (!response.ok) throw new Error("Translation failed.");
    return response.json();
  })
  .then(data => {
    if (data.error) {
      alert(data.error);
      return;
    }

    // Use the correct key from backend response
    const translatedAudioFile = data.translated_audio_file;

    if (!translatedAudioFile) {
      alert("Translated audio file not found in response.");
      return;
    }

    // Show translated audio preview
    translatedAudio.src = translatedAudioFile;
    translatedAudio.style.display = "block";
    translatedAudio.load();
    translatedAudio.play();

    // Add translated audio entry to history log
    const historyItem = document.createElement("div");
    historyItem.className = "history-item";

    const timestamp = new Date().toLocaleTimeString();

    historyItem.innerHTML = `
      <div class="history-list1">
        <p><strong>Language:</strong> ${lang.toUpperCase()}</p>
        <p><strong>Time:</strong> ${timestamp}</p>
      </div>
      <div class="history-list2">
        <p><strong>Translated Audio:</strong></p>
        <audio controls src="${translatedAudioFile}" class="history-audio"></audio>
      </div>
    `;

    historyLog.prepend(historyItem);
  })
  .catch(error => {
    console.error("Error during translation:", error);
    alert("Translation failed. Please try again.");
  });
});

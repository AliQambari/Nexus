const recordBtn = document.getElementById('record');
const stopBtn = document.getElementById('stop');
const transcription = document.getElementById('transcription');

let mediaRecorder;
let audioChunks = [];

recordBtn.addEventListener('click', async () => {
    recordBtn.disabled = true;
    stopBtn.disabled = false;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.addEventListener('dataavailable', (event) => {
        audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener('stop', async () => {
        const audioBlob = new Blob(audioChunks, { 'type': 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            const base64data = reader.result;
            $.post('/transcribe', { audio_data: base64data }, (data) => {
                transcription.textContent = data.text || data.error;
            });
        };
    });
});

stopBtn.addEventListener('click', () => {
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    mediaRecorder.stop();
    audioChunks = [];
});

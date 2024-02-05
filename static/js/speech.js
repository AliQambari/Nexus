var recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'fa-IR';

var startBtn = document.getElementById('startBtn');
var stopBtn = document.getElementById('stopBtn');
var submitBtn = document.getElementById('submitBtn');
var transcription = document.getElementById('transcription');
var wordBoxes = document.getElementById('wordBoxes');

function createWordBox(word) {
    var wordBox = document.createElement('span');
    wordBox.innerHTML = word;
    wordBox.classList.add('word-box');
    wordBoxes.appendChild(wordBox);
}

function clearWordBoxes() {
    while (wordBoxes.firstChild) {
        wordBoxes.removeChild(wordBoxes.firstChild);
    }
}

startBtn.addEventListener('click', function() {
    startBtn.disabled = true;
    stopBtn.disabled = false;
    submitBtn.disabled = true;
    transcription.value = '';
    recognition.start();
});

stopBtn.addEventListener('click', function() {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    recognition.stop();
});

submitBtn.addEventListener('click', function() {
    clearWordBoxes();
    var words = transcription.value.trim().split(' ');
    for (var i = 0; i < words.length; i++) {
        createWordBox(words[i]);
    }
});

recognition.onresult = function(event) {
    var interimTranscription = '';
    for (var i = event.resultIndex; i < event.results.length; i++) {
        var transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
            transcription.value += transcript + ' ';
        } else {
            interimTranscription += transcript;
        }
    }
    console.log(interimTranscription);
    if (transcription.value.trim() !== '') {
        submitBtn.disabled = false;
    }
};

recognition.onend = function() {
    startBtn.disabled = false;
    stopBtn.disabled = true;
};

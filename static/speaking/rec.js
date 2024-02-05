        const startRecordButton = document.getElementById('startRecord');
        const stopRecordButton = document.getElementById('stopRecord');
        const transcriptionInput = document.getElementById('transcriptionInput');
        const transcriptionForm = document.getElementById('transcriptionForm');
        const transcriptionText = document.getElementById('transcription');
        const improvedTranscription = document.getElementById('improvedTranscription');

        let recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let transcription = '';

        recognition.onresult = (event) => {
            let interimTranscription = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    transcription += event.results[i][0].transcript;
                } else {
                    interimTranscription += event.results[i][0].transcript;
                }
            }
            transcriptionText.textContent = transcription;
        };

        recognition.onend = () => {
            stopRecordButton.style.display = 'none';
            startRecordButton.style.display = 'block';
            transcriptionInput.value = transcription;
        };

        startRecordButton.addEventListener('click', () => {
            transcription = '';
            recognition.start();
            startRecordButton.style.display = 'none';
            stopRecordButton.style.display = 'block';
        });

        stopRecordButton.addEventListener('click', () => {
            recognition.stop();
        });

        transcriptionForm.addEventListener('submit', (event) => {
            if (transcription.length === 0) {
                alert('Please record something before submitting.');
                event.preventDefault();
            }
        });
        
        function displayImprovedTranscription(improvedText) {
            improvedTranscription.textContent = improvedText;
        }
   
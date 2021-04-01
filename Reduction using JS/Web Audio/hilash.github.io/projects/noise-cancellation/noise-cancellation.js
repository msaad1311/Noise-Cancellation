//https://www.mathworks.com/videos/active-noise-control-from-modeling-to-real-time-prototyping-1561451814853.html
//https://iopscience.iop.org/article/10.1088/1757-899X/308/1/012039/pdf

//var drawGraph = import("./graph.js");
var { clearBackground, drawLine, drawGraph } = import("./graph.js");
var initUserMediaFromBrowser = import("./audio-utils.js");
var rec0;
var rec1;

audioCtx = new (window.AudioContext || window.webkitAudioContext)();

class NoiseCancellationSimulator {
  constructor() {
    this._canvas = document.querySelector(".noise-cancellation-canvas");
    this.isPlaying = false;
    this._outputWave = true;
    this._outputAntiWave = true;
    this._antiWaveAmplitude = 100.0; // Reduction level
    this._antiWavePhase = 0;

    this._microphoneStream = null;
    this._microphone = null;
  }

  async play() {
    try {
      
    
    this.analyser1 = audioCtx.createAnalyser();
    this.analyser2 = audioCtx.createAnalyser();
   
    await this._initMicrophone();
    await this._initNoiseReducer();
    
    this._microphone.connect(this.noiseReducer);
    this.noiseReducer.connect(audioCtx.destination)
    rec0 = new Recorder(this._microphone,{numChannels:1});
    rec1 = new Recorder(this.noiseReducer,{numChannels:1});
    rec0.record()
    rec1.record()
    console.log("Recoridng started")
    // console.log("Microfone",this._microphone)
    // console.log("reducer",this.noiseReducer)

    if (this._outputWave) {
      this._microphone.connect(this.analyser1);
    }

    if (this._outputAntiWave) {
      this.noiseReducer.connect(this.analyser2);
    }
    this.visualize();
  } catch (error) {
      console.log(error);
  }
  }

  async _initMicrophone(){
    console.log('initializing microfone')
    initUserMediaFromBrowser();

    if (!navigator.mediaDevices.getUserMedia) {
      console.log("getUserMedia not supported on your browser!");
    }
    let constraints = { audio: true };
    this._microphoneStream = await navigator.mediaDevices.getUserMedia(
      constraints
    );
    console.log(this._microphoneStream);
    this._microphone = audioCtx.createMediaStreamSource(
      this._microphoneStream
    );
  }

  async _initNoiseReducer() {
    await audioCtx.audioWorklet.addModule("./noise-cancellation-processor.js");
    this.noiseReducer = new AudioWorkletNode(
      audioCtx,
      "noise-cancellation-processor"
    );

    this.antiWaveAmplitude = this._antiWaveAmplitude;
    this.antiWavePhase = this._antiWavePhase;
  }

  stop1() {
    this._disconnectMicrophone();
    this._disconnectNoiseReducer();
    window.cancelAnimationFrame(this.drawHandler);
    rec0.stop();
    rec0.exportWAV(this.createDownloadLink0)

    rec1.stop()
    rec1.exportWAV(this.createDownloadLink1)
  }

  createDownloadLink0(blob) {
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');
    //add controls to the <audio> element 
    au.controls = true;
    au.src = url;
    //link the a element to the blob 
    link.href = url;
    link.download = new Date().toISOString() + '.wav';
    link.innerHTML = link.download;
    //add the new audio and a elements to the li element 
    li.appendChild(au);
    li.appendChild(link);
    //add the li element to the ordered list 
    recordingsList0.appendChild(li);
  }

  createDownloadLink1(blob) {
    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');
    //add controls to the <audio> element 
    au.controls = true;
    au.src = url;
    //link the a element to the blob 
    link.href = url;
    link.download = new Date().toISOString() + '.wav';
    link.innerHTML = link.download;
    //add the new audio and a elements to the li element 
    li.appendChild(au);
    li.appendChild(link);
    //add the li element to the ordered list 
    recordingsList1.appendChild(li);
  }

  _disconnectMicrophone(){
    console.log('into the discount')
    console.log(this._microphoneStream)
    this._microphoneStream.getTracks().forEach(function(track) {
      track.stop();
    });
    this._microphone.disconnect();
  }

  _disconnectNoiseReducer(){
    this.noiseReducer.disconnect();
  }

  toggle() {
    console.log('toggled');
    console.log(this.isPlaying);
    if (this.isPlaying) {
      this.stop1();
    } else {
      this.play();
    }
    this.isPlaying = !this.isPlaying;
  }

  set outputWave(value) {
    this._outputWave = value;
    if (this.isPlaying) {
      this.stop1();
      this.play();
    }
  }

  set outputAntiWave(value) {
    this._outputAntiWave = value;
    if (this.isPlaying) {
      this.stop1();
      this.play();
    }
  }

  set antiWavePhase(value) {
    this._antiWavePhase = value
    const phaseParam =this.noiseReducer.parameters.get('phase')
    phaseParam.setValueAtTime(this._antiWavePhase, audioCtx.currentTime)
  }

  set antiWaveAmplitude(value) {
    this._antiWaveAmplitude = value
    const amplitudeParam =this.noiseReducer.parameters.get('amplitude')
    amplitudeParam.setValueAtTime(this._antiWaveAmplitude, audioCtx.currentTime)
  }

  visualize() {
    this.analyser1.fftSize = 2048;
    this.analyser2.fftSize = 2048;
    var bufferLength = this.analyser1.fftSize;
    var buffer1 = new Uint8Array(bufferLength);
    var buffer2 = new Uint8Array(bufferLength);

    clearBackground(this._canvas);

    this.draw = function() {
      this.drawHandler = requestAnimationFrame(this.draw);
      clearBackground(this._canvas);
      if (this._outputWave) {
        this.analyser1.getByteTimeDomainData(buffer1);
        drawLine(this._canvas, bufferLength, buffer1, false, "blue");
      }
      if (this._outputAntiWave) {
        this.analyser2.getByteTimeDomainData(buffer2);
        drawLine(this._canvas, bufferLength, buffer2, false, "red");
      }
    }.bind(this); // nice solution for requestAnimationFrame + this:  https://stackoverflow.com/a/32834390
    this.draw();
  }
}

const audioContext = new AudioContext();

let noiseGate = new NoiseGateNode(audioContext);
console.log(noiseGate)

audioCtx = new (window.AudioContext || window.webkitAudioContext)();
navigator.mediaDevices.getUserMedia({ audio: true })
.then(function(stream) {
    console.log(this.audioCtx)
  let source = this.audioCtx.createMediaStreamSource(stream);
  let noiseGate = new NoiseGateNode(audioContext);
  source.connect(noiseGate);
  noiseGate.connect(audioContext.destination);
});
// import {NoiseGateNode} from 'index.js';
const audioContext = new AudioContext();
// var NoiseGateNode = require('noise-gate')
// let noiseGate1 = new NoiseGateNode(audioContext);
// console.log(noiseGate1)

// context = new (window.AudioContext || window.webkitAudioContext)();
navigator.mediaDevices.getUserMedia({ audio: true })
.then(function(stream) {
    console.log(audioContext)
  let source = audioContext.createMediaStreamSource(stream);
  let noiseGate = new NoiseGateNode(audioContext);
  source.connect(noiseGate);
  noiseGate.connect(audioContext.destination);
});
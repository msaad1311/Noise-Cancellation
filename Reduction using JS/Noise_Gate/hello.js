//Load HTTP module
const http = require("http");
const NoiseGateNode = require("noise-gate");
// const AudioContext = require("noise-gate");
const hostname = '127.0.0.1';
const port = 3000;
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioCtx = new AudioContext();
//Create HTTP server and listen on port 3000 for requests
const server = http.createServer((req, res) => {

// import {NoiseGateNode} from 'index.js';

// let noiseGate1 = new NoiseGateNode(audioContext);
// console.log(noiseGate1)

// audioCtx = new (window.AudioContext || window.webkitAudioContext)();
navigator.mediaDevices.getUserMedia({ audio: true })
.then(function(stream) {
    console.log(this.context)
  let source = this.context.createMediaStreamSource(stream);
  let noiseGate = new NoiseGateNode(audioContext);
  source.connect(noiseGate);
  noiseGate.connect(audioContext.destination);
});

  //Set the response HTTP header with HTTP status and Content type
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World\n');
});

//listen for request on port 3000, and as a callback function have the port listened on logged
server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
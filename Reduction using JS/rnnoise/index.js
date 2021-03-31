const rnnoise = require("rnnoise");

const denoisedBufLength = rnnoise.suppress(
	  "mixedTester0.wav",
	"asdf.wav"
);

console.log(`Denoised buffer length: ${denoisedBufLength} bytes`);

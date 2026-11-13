/* Offline SenseVoice bridge for Android ARM64. No network, recording or HA control.
 * Build against the sherpa-onnx C API v2.0.1 with Android NDK (API24).
 * API intentionally uses PCM16 to avoid Python NumPy and unnecessary copies.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sherpa-onnx/c-api/c-api.h"
static const SherpaOnnxOfflineRecognizer *recognizer = NULL;
int zuk_sensevoice_init(const char *model, const char *tokens, int threads) {
  if (recognizer) return 0;
  if (!model || !tokens || threads < 1 || threads > 4) return -1;
  SherpaOnnxOfflineRecognizerConfig config = {0};
  config.feat_config.sample_rate = 16000;
  config.feat_config.feature_dim = 80;
  config.model_config.sense_voice.model = model;
  config.model_config.sense_voice.language = "zh";
  config.model_config.sense_voice.use_itn = 1;
  config.model_config.tokens = tokens;
  config.model_config.provider = "cpu";
  config.model_config.num_threads = threads;
  config.decoding_method = "greedy_search";
  recognizer = SherpaOnnxCreateOfflineRecognizer(&config);
  return recognizer ? 0 : -2;
}
int zuk_sensevoice_recognize_pcm16(const int16_t *samples, int n, char *out, int out_len) {
  if (!recognizer || !samples || !out || out_len < 2 || n < 1600 || n > 16000 * 9) return -1;
  float *audio = (float *)malloc((size_t)n * sizeof(float));
  if (!audio) return -2;
  for (int i=0; i<n; ++i) audio[i] = (float)samples[i] / 32768.0f;
  const SherpaOnnxOfflineStream *stream = SherpaOnnxCreateOfflineStream(recognizer);
  if (!stream) { free(audio); return -3; }
  SherpaOnnxAcceptWaveformOffline(stream, 16000, audio, n);
  free(audio);
  SherpaOnnxDecodeOfflineStream(recognizer, stream);
  const SherpaOnnxOfflineRecognizerResult *result = SherpaOnnxGetOfflineStreamResult(stream);
  if (!result) { SherpaOnnxDestroyOfflineStream(stream); return -4; }
  const char *s = result->text ? result->text : "";
  size_t size = strlen(s);
  if (size >= (size_t)out_len) size = (size_t)out_len - 1;
  memcpy(out, s, size); out[size] = '\0';
  SherpaOnnxDestroyOfflineRecognizerResult(result);
  SherpaOnnxDestroyOfflineStream(stream);
  return (int)size;
}
void zuk_sensevoice_shutdown(void) {
  if (recognizer) SherpaOnnxDestroyOfflineRecognizer(recognizer);
  recognizer = NULL;
}
